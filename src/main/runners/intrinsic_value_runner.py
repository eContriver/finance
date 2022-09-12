# ------------------------------------------------------------------------------
#  Copyright 2021-2022 eContriver LLC
#  This file is part of Finance from eContriver.
#  -
#  Finance from eContriver is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  any later version.
#  -
#  Finance from eContriver is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  -
#  You should have received a copy of the GNU General Public License
#  along with Finance from eContriver.  If not, see <https://www.gnu.org/licenses/>.
# ------------------------------------------------------------------------------

import logging
import os
from datetime import datetime
from math import ceil
from typing import Dict, Set, Optional, List

import numpy
import pandas
from numpy import median
from sklearn import linear_model

from main.application.adapter import AssetType, Adapter, get_common_start_time, get_common_end_time, \
    insert_column
from main.application.adapter_collection import AdapterCollection, filter_adapters
from main.application.argument import Argument, ArgumentKey
from main.application.runner import Runner, NoSymbolsSpecifiedException, validate_type, get_adapter_class, \
    get_asset_type_overrides, get_copyright_notice
from main.application.time_interval import TimeInterval
from main.application.value_type import ValueType
from main.common.locations import Locations, get_and_clean_timestamp_dir, file_link_format
from main.common.report import Report
from main.executors.parallel_executor import ParallelExecutor
from main.visual.visualizer import Visualizer


def to_dollars(value: float) -> str:
    abs_value = abs(value)
    if numpy.isnan(abs_value):
        value_as_str = "{}".format(value)
    elif abs_value > 10000000000:
        value_as_str = "${:.1f}b".format(value / 1000000000)
    elif abs_value > 10000000:
        value_as_str = "${:.1f}m".format(value / 1000000)
    elif abs_value > 10000:
        value_as_str = "${:.1f}k".format(value / 1000)
    else:
        value_as_str = "${:.2f}".format(value)
    return value_as_str


def to_abbrev(value: float) -> str:
    abs_value = abs(value)
    if numpy.isnan(abs_value):
        value_as_str = "{}".format(value)
    elif abs_value > 10000000000:
        value_as_str = "{:.1f}b".format(value / 1000000000)
    elif abs_value > 10000000:
        value_as_str = "{:.1f}m".format(value / 1000000)
    elif abs_value > 10000:
        value_as_str = "{:.1f}k".format(value / 1000)
    else:
        value_as_str = "{:.2f}".format(value)
    return value_as_str


def to_percent(value: float) -> str:
    if numpy.isnan(value):
        value_as_str = "{}".format(value)
    else:
        value_as_str = "{:.2f}%".format(value * 100)
    return value_as_str


def report_common_dividends(common_dividends: pandas.Series) -> str:
    report = "dividends: "
    for date, common_dividend in common_dividends.iteritems():
        report += "{}: {}  ".format(date.strftime("%Y-%m-%d"), to_dollars(common_dividend))
    return report


def calculate_common_dividend(earnings: pandas.Series, payout_ratio: float) -> pandas.Series:
    common_dividends = pandas.Series()
    for date, earnings in earnings.iteritems():
        common_dividends[date] = earnings * payout_ratio
    return common_dividends


def report_irr(future_earnings: pandas.Series, common_dividends, at_price, avg_price, max_price, median_price,
               min_price, multiple):
    cash_flows = [at_price * -1]
    for date, earnings in future_earnings.iteritems():
        cash_flows += [common_dividends[date]]
    max_irr = round(numpy.irr(cash_flows + [max_price]) * 100, 4) * multiple
    irr_report = "max={}%".format(max_irr)
    avg_irr = round(numpy.irr(cash_flows + [avg_price]) * 100, 4) * multiple
    irr_report += " avg={}%".format(avg_irr)
    median_irr = round(numpy.irr(cash_flows + [median_price]) * 100, 4) * multiple
    irr_report += " med={}%".format(median_irr)
    min_irr = round(numpy.irr(cash_flows + [min_price]) * 100, 4) * multiple
    irr_report += " min={}%".format(min_irr)
    return irr_report


def predict_value_type_linear(collection: AdapterCollection, symbol: str, value_type: ValueType,
                              future_time: datetime) -> float:
    adapter: Adapter = filter_adapters(collection.adapters, symbol, value_type)
    start_time = get_common_start_time(adapter.data)
    end_time = get_common_end_time(adapter.data)
    column: pandas.Series = adapter.get_column_between(start_time, end_time, value_type)
    column.dropna(inplace=True)
    column = column.sort_index(ascending=True)
    prediction = predict_value_linear(column, future_time)
    return prediction


def predict_value_linear(column: pandas.Series, future_time: datetime) -> float:
    column = column.replace([numpy.inf, -numpy.inf], numpy.nan).dropna()
    start_time = min(column.index)
    days_from_start = (column.index - start_time).days.to_numpy()
    y = column.values
    x = days_from_start.reshape(-1, 1)
    model = linear_model.LinearRegression().fit(x, y)
    future_days = (future_time - start_time).days
    predictions = model.predict([[future_days]])
    return predictions[0]


def get_cash_flow_value_types() -> List[ValueType]:
    value_types = [ValueType.CASH_FLOW, ValueType.NET_INCOME, ValueType.DIVIDENDS]
    return value_types


def get_income_value_types() -> List[ValueType]:
    value_types = [ValueType.REVENUE]
    return value_types


def get_earnings_value_types() -> List[ValueType]:
    value_types = [ValueType.EPS]
    return value_types


def get_balance_sheet_value_types() -> List[ValueType]:
    value_types = [
        ValueType.ASSETS,
        ValueType.LIABILITIES,
        ValueType.EQUITY,
        ValueType.LONG_DEBT,
        ValueType.SHORT_DEBT,
    ]
    return value_types


def get_price_value_types() -> List[ValueType]:
    value_types = [ValueType.HIGH, ValueType.LOW, ValueType.CLOSE]
    return value_types


def get_prices_from_earnings(earnings_per_share, max_pe, median_pe, avg_pe, min_pe) -> (float, float, float, float):
    max_price = max_pe * earnings_per_share
    max_price = -1.0 * max_price if (max_pe < 0) and (earnings_per_share < 0) else max_price
    avg_price = avg_pe * earnings_per_share
    avg_price = -1.0 * avg_price if (avg_pe < 0) and (earnings_per_share < 0) else avg_price
    median_price = median_pe * earnings_per_share
    median_price = -1.0 * median_price if (median_pe < 0) and (earnings_per_share < 0) else median_price
    min_price = min_pe * earnings_per_share
    min_price = -1.0 * min_price if (min_pe < 0) and (earnings_per_share < 0) else min_price
    return max_price, avg_price, median_price, min_price


def convert_formats(df):
    df[ValueType.REVENUE] = df[ValueType.REVENUE].apply(to_dollars)
    df[ValueType.CASH_FLOW] = df[ValueType.CASH_FLOW].apply(to_dollars)
    df[ValueType.ASSETS] = df[ValueType.ASSETS].apply(to_dollars)
    df[ValueType.SHARES] = df[ValueType.SHARES].apply(to_abbrev)
    df[ValueType.LIABILITIES] = df[ValueType.LIABILITIES].apply(to_dollars)
    df[ValueType.LONG_DEBT] = df[ValueType.LONG_DEBT].apply(to_dollars)
    df[ValueType.SHORT_DEBT] = df[ValueType.SHORT_DEBT].apply(to_dollars)
    df[ValueType.EQUITY] = df[ValueType.EQUITY].apply(to_dollars)
    df[ValueType.EPS] = df[ValueType.EPS].apply(to_dollars)
    df[ValueType.NET_INCOME] = df[ValueType.NET_INCOME].apply(to_dollars)
    df[ValueType.DIVIDENDS] = df[ValueType.DIVIDENDS].apply(to_dollars)
    df[ValueType.HIGH] = df[ValueType.HIGH].apply(to_dollars)
    df[ValueType.LOW] = df[ValueType.LOW].apply(to_dollars)
    df[ValueType.CLOSE] = df[ValueType.CLOSE].apply(to_dollars)
    # if IntrinsicValueRunner.LOW_PE not in df.index:
    #     df[IntrinsicValueRunner.LOW_PE] = numpy.nan
    df[IntrinsicValueRunner.LOW_PE] = df[IntrinsicValueRunner.LOW_PE].apply(to_abbrev)
    # if IntrinsicValueRunner.HIGH_PE not in df.index:
    #     df[IntrinsicValueRunner.HIGH_PE] = numpy.nan
    df[IntrinsicValueRunner.HIGH_PE] = df[IntrinsicValueRunner.HIGH_PE].apply(to_abbrev)
    # if IntrinsicValueRunner.ROE not in df.index:
    #     df[IntrinsicValueRunner.ROE] = numpy.nan
    df[IntrinsicValueRunner.ROE] = df[IntrinsicValueRunner.ROE].apply(to_percent)


def report_order(df):
    columns = [ValueType.SHARES]
    columns += get_balance_sheet_value_types()
    columns += get_earnings_value_types()
    columns += get_income_value_types()
    columns += get_cash_flow_value_types()
    columns += [IntrinsicValueRunner.LOW_PE, IntrinsicValueRunner.HIGH_PE, IntrinsicValueRunner.ROE]
    df_ordered = df[columns]  # reorders using order of values in value_types
    return df_ordered


class IntrinsicValueRunner(Runner):
    HIGH_PE: str = 'High P/E'
    LOW_PE: str = 'Low P/E'
    ROE: str = 'ROE'

    symbol: Optional[str]
    adapter_class: Optional[type]
    base_symbol: str
    graph: bool
    fundamentals_interval: TimeInterval
    price_interval: TimeInterval
    asset_type_overrides: Dict[str, AssetType]

    def __init__(self):
        super().__init__()
        self.symbol = None
        self.adapter_class = None
        self.base_symbol = 'USD'
        self.graph = True
        self.price_interval = TimeInterval.MONTH
        self.fundamentals_interval = TimeInterval.YEAR
        self.asset_type_overrides = {}

    def start(self, locations: Locations):
        logging.info("#### Starting intrinsic value runner...")
        success = True
        # Multiple collections == Multiple plots : Each collection is in it's own dict entry under the query type
        # collections = self.multiple_collections(symbols, overrides, base_symbol, adapter_class, interval, today)
        # Single collection == Single plots      : There is one collection in the dict with the key Fundamentals
        collections: Dict[str, AdapterCollection] = self.single_collection(self.symbol)
        df = self.report_collections(locations, collections)
        if self.graph:
            # self.plot_collections(locations, collections, self.fundamentals_interval)
            df[get_balance_sheet_value_types()].plot.bar()
            df[get_earnings_value_types()].plot()
            df[get_cash_flow_value_types()].plot()
            df[get_income_value_types()].bar.plot()
        return success

    def get_config(self) -> Dict:
        asset_type_overrides = {}
        for symbol, asset_type in self.asset_type_overrides.items():
            asset_type_overrides[symbol] = asset_type.name
        config = {
            'adapter_class':         self.adapter_class.__name__,
            'base_symbol':           self.base_symbol,
            'symbol':                self.symbol,
            'graph':                 self.graph,
            'fundamentals_interval': self.fundamentals_interval.value,
            'price_interval':        self.price_interval.value,
            'asset_type_overrides':  asset_type_overrides,
        }
        return config

    def set_from_config(self, config, config_path):
        self.asset_type_overrides = get_asset_type_overrides(
            config['asset_type_overrides'] if 'asset_type_overrides' in config else {})
        self.symbol = config['symbol']
        self.adapter_class = get_adapter_class(config['adapter_class'])
        self.base_symbol = config['base_symbol']
        self.fundamentals_interval = TimeInterval(config['fundamentals_interval'])
        self.price_interval = TimeInterval(config['price_interval'] if 'price_interval' in config else 'monthly')
        self.graph = config['graph'] if 'graph' in config else True
        self.check_member_variables(config_path)

    def check_member_variables(self, config_path: str):
        validate_type('symbol', self.symbol, str, config_path)
        if not self.symbol:
            raise NoSymbolsSpecifiedException(f"Please specify at least one symbol in: {config_path}")
        # if len(self.symbol) > 1:
        #     raise TooManySymbolsSpecifiedException(f"Please specify only one symbol in (found: {self.symbol}): {config_path}")

    def get_run_name(self):
        return f"{self.symbol}_{self.fundamentals_interval.value}_{self.adapter_class.__name__}"

    def single_collection(self, symbol: str) -> Dict[str, AdapterCollection]:
        collection: AdapterCollection = AdapterCollection()
        collection.add(self.create_price_adapter(symbol))
        collection.add(self.create_fundamentals_adapter(symbol))
        # collection.set_all_cache_key_dates(datetime(year=2021, month=6, day=25))
        collection.retrieve_all_data()
        return {'Fundamentals': collection}

    def create_price_adapter(self, symbol: str):
        adapter = self.new_adapter(symbol)
        adapter.request_value_types = [
            ValueType.HIGH,
            ValueType.OPEN,
            ValueType.CLOSE,
            ValueType.LOW,
        ]
        adapter.add_argument(Argument(ArgumentKey.INTERVAL, self.price_interval))
        return adapter

    def create_fundamentals_adapter(self, symbol):
        adapter = self.new_adapter(symbol)
        value_types = [ValueType.SHARES]
        value_types += get_balance_sheet_value_types()
        value_types += get_earnings_value_types()
        value_types += get_income_value_types()
        value_types += get_cash_flow_value_types()
        adapter.request_value_types = value_types
        adapter.add_argument(Argument(ArgumentKey.INTERVAL, self.fundamentals_interval))
        return adapter

    def new_adapter(self, symbol) -> Adapter:
        """
        Creates a new adapter with common configuration for the different IV use cases
        :param symbol: The symbol to create the adapter for
        :return: The created adapter
        """
        adapter = self.adapter_class(symbol, asset_type=None)
        adapter.base_symbol = self.base_symbol
        # This was being used during testing, so that every day the cache was the same...
        # end_date = datetime(year=2021, month=7, day=3)
        end_date = datetime.now()
        adapter.add_argument(Argument(ArgumentKey.START_TIME, end_date - 10 * TimeInterval.YEAR.timedelta))
        adapter.add_argument(Argument(ArgumentKey.END_TIME, end_date))
        adapter.cache_key_date = end_date
        adapter.asset_type = self.asset_type_overrides[symbol] if symbol in self.asset_type_overrides else None
        return adapter

    # def multiple_collections(self, symbols, asset_type_overrides, base_symbol, adapter_class, interval, cache_date):
    #     query_types = [QueryType.INCOME, QueryType.EARNINGS, QueryType.CASH_FLOW, QueryType.BALANCE_SHEET]
    #     handles: Dict[QueryType, List[AdapterCollection]] = {}
    #     for query_type in query_types:
    #         handles[query_type] = []
    #         for symbol in symbols:
    #             handles[query_type].append(AdapterCollection(symbol))
    #     # builder: CollectionBuilder = CollectionBuilder(symbols)
    #     self.add_income_adapter_coln(
    #         # builder.add_series_adapter_coln()
    #         handles[QueryType.INCOME], adapter_class, base_symbol, interval, asset_type_overrides, cache_date)
    #     self.add_earnings_adapter_coln(
    #         # builder.add_series_adapter_coln()
    #         handles[QueryType.EARNINGS], adapter_class, base_symbol, interval, asset_type_overrides, cache_date)
    #     self.add_balance_sheet_adapter_coln(
    #         # builder.add_series_adapter_coln()
    #         handles[QueryType.BALANCE_SHEET], adapter_class, base_symbol, interval, asset_type_overrides, cache_date)
    #     self.add_cash_flow_adapter_coln(
    #         # builder.add_series_adapter_coln()
    #         handles[QueryType.CASH_FLOW], adapter_class, base_symbol, interval, asset_type_overrides, cache_date)
    #     collections = {}
    #     for query_type in query_types:
    #         collections[query_type.name] = self.get_collection(handles[query_type], base_symbol)
    #     return collections

    @staticmethod
    def func(x, a, b, c, d):
        """
        A quadratic function used to fit a curve
        :param x:
        :param a:
        :param b:
        :param c:
        :param d:
        :return:
        """
        return a * (x ** 3) + b * (x ** 2) + c * x + d

    # @staticmethod
    # def extrapolate(s: pandas.DataFrame) -> pandas.DataFrame:
    #     # Initial parameter guess, just to kick off the optimization
    #     guess = (0.5, 0.5, 0.5, 0.5)
    #
    #     # Create copy of data to remove NaNs for curve fitting
    #     fit_df = s.dropna()
    #
    #     # Place to store function parameters for each column
    #     col_params = {}
    #
    #     # Curve fit each column
    #     for col in fit_df.columns:
    #         # Get x & y
    #         x = fit_df.index.astype(int).values
    #         y = fit_df[col].values
    #         # Curve fit column and get curve parameters
    #         params = curve_fit(IntrinsicValueRunner.func, x, y, guess)
    #         # Store optimized parameters
    #         col_params[col] = params[0]
    #
    #     # Extrapolate each column
    #     for col in s.columns:
    #         # Get the index values for NaNs in the column
    #         x = s[pandas.isnull(s[col])].index.astype(int).values
    #         # Extrapolate those points with the fitted function
    #         s[col][x] = IntrinsicValueRunner.func(x, *col_params[col])
    #
    #     return s
    #
    # @staticmethod
    # def extrapolate_linear(s):
    #     """
    #     https://github.com/pandas-dev/pandas/issues/31949
    #     :param s:
    #     :return:
    #     """
    #     s = s.copy()
    #     # Indices of not-nan values
    #     idx_nn = s.index[~s.isna()]
    #
    #     # At least two data points needed for trend analysis
    #     assert len(idx_nn) >= 2
    #
    #     # Outermost indices
    #     idx_l = idx_nn[0]
    #     idx_r = idx_nn[-1]
    #
    #     # Indices left and right of outermost values
    #     idx_ll = s.index[s.index < idx_l]
    #     idx_rr = s.index[s.index > idx_r]
    #
    #     # Derivative of not-nan indices / values
    #     v = s[idx_nn].diff()
    #
    #     # Left- and right-most derivative values
    #     v_l = v[1]
    #     v_r = v[-1]
    #     f_l = idx_l - idx_nn[1]
    #     f_r = idx_nn[-2] - idx_r
    #
    #     # Set values left / right of boundaries
    #     l_l = lambda idx: (idx_l - idx) / f_l * v_l + s[idx_l]
    #     l_r = lambda idx: (idx_r - idx) / f_r * v_r + s[idx_r]
    #     x_l = pd.Series(idx_ll).apply(l_l)
    #     x_l.index = idx_ll
    #     x_r = pd.Series(idx_rr).apply(l_r)
    #     x_r.index = idx_rr
    #     s[idx_ll] = x_l
    #     s[idx_rr] = x_r
    #
    #     return s

    def report_collections(self, locations: Locations, collections: Dict[str, AdapterCollection]) -> pandas.DataFrame:
        # A Collection can have multiple symbols tied to a variety of adapters, instead of iterating these right now,
        # we just support one, but if we want to do multiple then we can add support for it
        for name, collection in collections.items():
            eps_adapter = filter_adapters(collection.adapters, self.symbol, ValueType.EPS)
            eps_intervals: Set[TimeInterval] = set(
                [argument.value for argument in eps_adapter.arguments if argument.argument_key ==
                 ArgumentKey.INTERVAL])
            assert len(eps_intervals) == 1, "Expected to report on 1 interval for {}, but found: {}".format(
                ValueType.EPS, eps_intervals)
            interval: TimeInterval = list(eps_intervals)[0]

            value_types = [ValueType.SHARES]
            value_types += get_balance_sheet_value_types()
            value_types += get_earnings_value_types()
            value_types += get_income_value_types()
            value_types += get_cash_flow_value_types()
            value_types += get_price_value_types()

            output_dir = locations.get_output_dir(Report.camel_to_snake(self.__class__.__name__))
            report_name = f"{self.get_run_name()}.log"
            report_path = os.path.join(output_dir, report_name)
            report: Report = Report(report_path)

            report.log('-- Start report for {}'.format(self.symbol))
            report.log('\n'.join(get_copyright_notice()))

            unbound_df: pandas.DataFrame = collection.get_columns(self.symbol, value_types)

            # report.log("BEFORE...\n{}".format(unbound_df.to_string()))

            # udf: pandas.DataFrame = self.report_format(unbound_df)
            # report.log("BEFORE...\n{}".format(udf.to_string()))

            unbound_df.interpolate(method='time', inplace=True, limit_area='inside')
            # unbound_df.interpolate(method='time', inplace=True, limit_area='outside')

            first_time = get_common_start_time(unbound_df)
            last_time = get_common_end_time(unbound_df)
            report.log('Last time: {}  First time: {}'.format(last_time.strftime("%Y-%m-%d"),
                                                              first_time.strftime("%Y-%m-%d")))
            unbound_df = unbound_df.truncate(first_time, last_time)

            df: pandas.DataFrame = unbound_df

            # TODO: Where this is used, is it appropriate?
            outstanding_last_time = df[ValueType.SHARES].last_valid_index()
            outstanding = df.loc[outstanding_last_time, ValueType.SHARES]

            # get series data
            p_df = collection.get_columns(self.symbol, get_price_value_types())

            # merge series data into the data - match earnings dates using +/- 2 weeks
            df[ValueType.LOW] = ""
            df[ValueType.HIGH] = ""
            df[IntrinsicValueRunner.LOW_PE] = ""
            df[IntrinsicValueRunner.HIGH_PE] = ""
            for date in df.index:
                end_idx = p_df.index.get_loc(date, method='nearest')
                start_date = date - self.fundamentals_interval.timedelta
                start_idx = p_df.index.get_loc(start_date, method='nearest')
                df.loc[date, ValueType.LOW] = p_df.iloc[start_idx:end_idx + 1, :][ValueType.LOW].min()
                df.loc[date, ValueType.HIGH] = p_df.iloc[start_idx:end_idx + 1, :][ValueType.HIGH].max()
                # df.loc[date, ValueType.CLOSE] = p_df.iloc[end_idx, :][ValueType.CLOSE]

            # P/Es
            # NOTE: for quarterly, earnings are quarterly but prices are absolute: PE = Price /(Quarterly Earnings * 4)
            multiple = 4 if self.fundamentals_interval is TimeInterval.QUARTER else 1
            df.loc[:, IntrinsicValueRunner.LOW_PE] = df.loc[:, ValueType.LOW] / (df.loc[:, ValueType.EPS] * multiple)
            df.loc[:, IntrinsicValueRunner.HIGH_PE] = df.loc[:, ValueType.HIGH] / (df.loc[:, ValueType.EPS] * multiple)
            zero_negative_pe = True
            if zero_negative_pe:
                df.loc[df.loc[:, IntrinsicValueRunner.LOW_PE].lt(0), IntrinsicValueRunner.LOW_PE] = 0
                df.loc[df.loc[:, IntrinsicValueRunner.HIGH_PE].lt(0), IntrinsicValueRunner.HIGH_PE] = 0

            pe_ratios = df.loc[:, IntrinsicValueRunner.LOW_PE].tolist() + df.loc[:,
                                                                          IntrinsicValueRunner.HIGH_PE].tolist()
            # pe_ratios = [i for i in pe_ratios_org if i >= 0]
            # if len(pe_ratios_org) != len(pe_ratios):
            #     report.log("Negative P/E ratios are being removed for future calculations!")
            #     pe_ratios.append(0.00000001)  # we add 0 as a truncated version of the negatives
            # pe_ratios.dropna(inplace=True)

            # ROEs
            df.loc[:, IntrinsicValueRunner.ROE] = df.loc[:, ValueType.NET_INCOME] / (df.loc[:, ValueType.EQUITY])

            #################################################################################
            # Report now...
            report_df = self.report_format(df)
            report.log("Data table for intrinsic value calculation using {}...\n{}".format(
                self.fundamentals_interval, report_df.to_string()))

            predictions_df = pandas.DataFrame()
            future_start_time = last_time + interval.timedelta
            intervals = ceil((df.index.max() - df.index.min()) / interval.timedelta)
            for column in value_types:
                values = []
                indexes = []
                for it in range(intervals):
                    future_datetime = future_start_time + it * interval.timedelta
                    indexes.append(future_datetime)
                    values.append(predict_value_type_linear(collection, self.symbol, column, future_datetime))
                if column in [ValueType.SHORT_DEBT, ValueType.LONG_DEBT, ValueType.LIABILITIES,
                              ValueType.DIVIDENDS]:  # if debt trending to negative, then zero it
                    values = [value if value >= 0 else 0 for value in values]
                if column in [ValueType.SHARES]:  # if debt trending to negative, then zero it
                    values = [df.loc[last_time, ValueType.SHARES] for value in values]
                insert_column(predictions_df, column, indexes, values)

            for column in [IntrinsicValueRunner.LOW_PE, IntrinsicValueRunner.HIGH_PE, IntrinsicValueRunner.ROE]:
                values = []
                indexes = []
                for it in range(intervals):
                    future_datetime = future_start_time + it * interval.timedelta
                    indexes.append(future_datetime)
                    values.append(predict_value_linear(df.loc[:, column], future_datetime))
                insert_column(predictions_df, column, indexes, values)

            mean_msg = ""
            use_mean_eps = False
            if use_mean_eps:
                mean_eps = df.loc[:, ValueType.EPS].mean()
                predictions_df.loc[:, ValueType.EPS] = mean_eps
                mean_msg = " | mean EPS=${:.2f}".format(mean_eps)

            predictions_print = self.report_format(predictions_df)
            report.log("Data table of intrinsic value predictions using {}...\n{}".format(
                self.fundamentals_interval, predictions_print.to_string()))

            assets_last_time = df[ValueType.ASSETS].last_valid_index()
            liabilities_last_time = df[ValueType.LIABILITIES].last_valid_index()
            book_value = df.loc[assets_last_time, ValueType.ASSETS] - df.loc[
                liabilities_last_time, ValueType.LIABILITIES]
            assert book_value != 0.0, "Total Assets {} - Total Liabilities {} = {} (book value should not be 0, " \
                                      "it will lead to a divide by zero problem for book value growth rate " \
                                      "calculations)".format(df.loc[assets_last_time, ValueType.ASSETS],
                                                             df.loc[liabilities_last_time, ValueType.LIABILITIES],
                                                             book_value)
            future_end_time = predictions_df.index.max()
            predicted_book_value = predictions_df.loc[future_end_time, ValueType.EQUITY]
            report.log("book value: current={} (on {}) | prediction={} (for {})".format(
                to_dollars(book_value),
                assets_last_time.strftime("%Y-%m-%d"),
                to_dollars(predicted_book_value),
                future_end_time.strftime("%Y-%m-%d"),
            ))

            # NOTE: we could do this math on the dataframe instead of scalar, but we don't currently need it
            eps_last_time = df[ValueType.EPS].last_valid_index()
            earnings_per_share = df.loc[eps_last_time, ValueType.EPS]
            dividend_last_time = df[ValueType.DIVIDENDS].last_valid_index()
            dividends_per_share = df.loc[dividend_last_time, ValueType.DIVIDENDS] / outstanding
            payout_ratio = dividends_per_share / earnings_per_share
            # On a per fundamentals_interval period, can be yearly, can be quarterly
            retention_ratio = 1 - payout_ratio
            retention_ratio = 0.0 if retention_ratio < 0.0 else retention_ratio
            book_value_per_share = book_value / outstanding
            book_yield_per_share = earnings_per_share / book_value_per_share
            book_value_growth = book_yield_per_share * retention_ratio

            # Predicted ROE - Using a trend-line equivalent predict where ROE will be
            return_on_equity = predictions_df.loc[future_end_time, IntrinsicValueRunner.ROE]

            report.log(
                "dividend: payout={} (on {}) | div/share(DPS)=${:.2f} | DPS/EPS={:.2f}% | retained={:.2f}%".format(
                    to_dollars(df.loc[last_time, ValueType.DIVIDENDS]),
                    last_time.strftime("%Y-%m-%d"),
                    dividends_per_share,
                    payout_ratio * 100.0,
                    retention_ratio * 100.0,
                ))
            report.log(
                "book: value(BVPS)=${:.2f} (on {}) | EPS/BVPS(yield)={:.2f}% | yield*retained(growth)={:.2f}%".format(
                    book_value_per_share,
                    last_time.strftime("%Y-%m-%d"),
                    book_yield_per_share * 100.0,
                    book_value_growth * 100.0,
                ))

            max_pe = max(pe_ratios)
            avg_pe = sum(pe_ratios) / len(pe_ratios)
            median_pe = median(pe_ratios)
            min_pe = min(pe_ratios)

            # the predictions are from a linear regression and could be used, but instead we do as Buffet does:
            calculated_eps = predictions_df.loc[future_end_time, ValueType.EPS] * multiple
            # calculated_eps = future_earnings[future_end_time]  # predictions[ValueType.REPORTED_EPS]
            max_price, avg_price, median_price, min_price = get_prices_from_earnings(
                calculated_eps, max_pe, median_pe, avg_pe, min_pe)

            current_time = p_df.index.max()
            current_price = p_df.loc[current_time, ValueType.CLOSE]
            last_price = df.loc[last_time, ValueType.CLOSE]
            future_dividends: pandas.Series = calculate_common_dividend(predictions_df[ValueType.EPS], payout_ratio)
            report.log(report_common_dividends(future_dividends))

            future_price = "max={} avg={} med={} min={}".format(to_dollars(max_price),
                                                                to_dollars(avg_price),
                                                                to_dollars(median_price),
                                                                to_dollars(min_price),
                                                                )
            report.log("P/Es: max={:.2f} avg={:.2f} med={:.2f} min={:.2f} | ROE={:.2f}%{}".format(
                max_pe, avg_pe, median_pe, min_pe, return_on_equity * 100.0, mean_msg))
            report.log("future prices (P/Es * future EPS ${}): {} ({})".format(
                round(calculated_eps, 2), future_price, future_end_time.strftime("%Y-%m-%d")))
            future_earnings = predictions_df[ValueType.EPS]
            irr_last = report_irr(future_earnings, future_dividends, last_price,
                                  avg_price, max_price, median_price, min_price, multiple)
            report.log(
                "last IRR from {} ({}): {} on {}".format(to_dollars(last_price), last_time.strftime("%Y-%m-%d"),
                                                         irr_last, future_end_time.strftime("%Y-%m-%d")))
            irr_current = report_irr(future_earnings, future_dividends, current_price,
                                     avg_price, max_price, median_price, min_price, multiple)
            report.log(
                "current IRR from {} ({}): {} on {}".format(to_dollars(current_price),
                                                            current_time.strftime("%Y-%m-%d"),
                                                            irr_current, future_end_time.strftime("%Y-%m-%d")))
            max_current, avg_current, median_current, min_current = get_prices_from_earnings(
                earnings_per_share * multiple, max_pe, median_pe, avg_pe, min_pe)
            fair_price = "max={} avg={} med={} min={}".format(to_dollars(max_current),
                                                              to_dollars(avg_current),
                                                              to_dollars(median_current),
                                                              to_dollars(min_current),
                                                              )
            report.log("fair prices (P/Es * current EPS ${}): {} ({})".format(
                round(earnings_per_share, 2), fair_price, current_time.strftime("%Y-%m-%d")))

            price_to_book = current_price / book_value_per_share
            price_to_earnings = current_price / earnings_per_share
            cashflow_last_time = df[ValueType.CASH_FLOW].last_valid_index()
            cashflow_per_share = df.loc[cashflow_last_time, ValueType.CASH_FLOW] / outstanding
            price_to_cashflow = current_price / cashflow_per_share
            report.log("price/book={:.2f} | price/earnings={:.2f} | price/cash flow={:.2f}".format(
                price_to_book, price_to_earnings, price_to_cashflow))

            short_debt_last_time = df[ValueType.SHORT_DEBT].last_valid_index()
            long_debt_last_time = df[ValueType.LONG_DEBT].last_valid_index()
            debt = df.loc[short_debt_last_time, ValueType.SHORT_DEBT] + df.loc[long_debt_last_time, ValueType.LONG_DEBT]
            debt_to_equity_ratio = debt / df.loc[assets_last_time, ValueType.EQUITY]
            debt_to_assets_ratio = debt / df.loc[assets_last_time, ValueType.ASSETS]
            liabilities_to_assets_ratio = df.loc[assets_last_time, ValueType.LIABILITIES] / df.loc[
                assets_last_time, ValueType.ASSETS]
            report.log("debt/equity={:.2f}%".format(debt_to_equity_ratio * 100) +
                       " | liabilities/assets={:.2f}%".format(liabilities_to_assets_ratio * 100) +
                       " | debt/assets={:.2f}%".format(debt_to_assets_ratio * 100))

            report.log('-- End report for {}'.format(self.symbol))
            logging.info(f'Report file: {file_link_format(report_path)}')

            return df

    def report_format(self, df_orig):
        df = df_orig.copy()
        convert_formats(df)
        df = report_order(df)
        return df

    # @staticmethod
    # def get_data(adapter: Adapter) -> pandas.DataFrame:  # , value_types):
    #     df = adapter.data
    #     # flat_data, columns = adapter.get_all_data_flat()
    #     # df = pandas.DataFrame.from_dict(flat_data, orient='index', columns=columns)
    #     # df.index.name = 'Date'
    #     first_date = df.index[-1]
    #     df[FundamentalRunner.DAYS_FROM_START] = (df.index - first_date).days
    #     return df

    def plot_collections(self, locations: Locations, collections, interval):
        visual_date_dir = get_and_clean_timestamp_dir(locations.get_output_dir('visuals'))
        # executor = SequentialExecutor(visual_date_dir)
        executor = ParallelExecutor(visual_date_dir)
        for name, collection in collections.items():
            title = "{} {}".format(list(set([adapter.symbol for adapter in collection.adapters])),
                                   self.get_title_string(interval, name))
            visualizer: Visualizer = Visualizer(str(title), collection)
            # visualizer.annotate_canceled_orders = True
            # visualizer.annotate_opened_orders = True
            # visualizer.annotate_open_prices = True
            # visualizer.annotate_close_prices = True
            # visualizer.draw_high_prices = True
            # visualizer.draw_low_prices = True
            # visualizer.draw_open_prices = True
            # visualizer.draw_close_prices = True
            executor.add(visualizer.plot_all, (), str(title).replace(' ', '_'))
        executor.start()

    # @staticmethod
    # def get_collection(handles, base_symbol):
    #     collection: SymbolCollection = SymbolCollection(base_symbol)
    #     for symbol_handle in handles:
    #         collection.add_symbol_handle(symbol_handle)
    #     collection.add_all_columns()
    #     return collection

    @staticmethod
    def get_title_string(interval, query_type_name):
        title = []
        words = [interval.value]
        words += str(query_type_name.lower()).replace('_', ' ').split(' ')
        for word in words:
            title.append(word.capitalize())
        return ' '.join(title)
