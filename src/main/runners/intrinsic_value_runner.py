#  Copyright 2021 eContriver LLC
#  This file is part of Finance from eContriver.
#
#  Finance from eContriver is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  any later version.
#
#  Finance from eContriver is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Finance from eContriver.  If not, see <https://www.gnu.org/licenses/>.
import logging
import os
from datetime import datetime
from math import ceil
from typing import Dict, Set, Optional, List

import numpy
import pandas
from numpy import median
from sklearn import linear_model

from main.application.adapter import TimeInterval, AssetType, Adapter, get_common_start_time, get_common_end_time
from main.application.adapter_collection import AdapterCollection, filter_adapters
from main.application.argument import Argument, ArgumentType
from main.application.value_type import ValueType
from main.common.report import Report
from main.common.locations import Locations, get_and_clean_timestamp_dir, file_link_format
from main.executors.parallel_executor import ParallelExecutor
from main.application.runner import Runner, NoSymbolsSpecifiedException, validate_type, get_adapter_class, \
    get_asset_type_overrides, get_copyright_notice
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


def report_common_dividends(common_dividends):
    report = "  Common Dividends - "
    for date, common_dividend in common_dividends.items():
        report += "{}: {}  ".format(date.strftime("%Y-%m-%d"), to_dollars(common_dividend))
    return report


def calculate_common_dividend(calculated_earnings, payout_ratio):
    common_dividends = {}
    for date, earnings in calculated_earnings.items():
        common_dividends[date] = earnings * payout_ratio
    return common_dividends


def report_irr(future_earnings, common_dividends, at_price, avg_price, max_price, median_price, min_price):
    cash_flows = [at_price * -1]
    for date, earnings in future_earnings.items():
        cash_flows += [common_dividends[date]]
    max_irr = round(numpy.irr(cash_flows + [max_price]) * 100, 4)
    irr_report = "Max: {}%".format(max_irr)
    avg_irr = round(numpy.irr(cash_flows + [avg_price]) * 100, 4)
    irr_report += "  Average: {}%".format(avg_irr)
    median_irr = round(numpy.irr(cash_flows + [median_price]) * 100, 4)
    irr_report += "  Median: {}%".format(median_irr)
    min_irr = round(numpy.irr(cash_flows + [min_price]) * 100, 4)
    irr_report += "  Min: {}%".format(min_irr)
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


class IntrinsicValueRunner(Runner):
    HIGH_PE: str = 'High P/E'
    LOW_PE: str = 'Low P/E'

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
            'adapter_class': self.adapter_class.__name__,
            'base_symbol': self.base_symbol,
            'symbol': self.symbol,
            'graph': self.graph,
            'fundamentals_interval': self.fundamentals_interval.value,
            'price_interval': self.price_interval.value,
            'asset_type_overrides': asset_type_overrides,
        }
        return config

    def set_from_config(self, config, config_path):
        self.asset_type_overrides = get_asset_type_overrides(config['asset_type_overrides'])
        self.symbol = config['symbol']
        self.adapter_class = get_adapter_class(config['adapter_class'])
        self.base_symbol = config['base_symbol']
        self.fundamentals_interval = TimeInterval(config['fundamentals_interval'])
        self.price_interval = TimeInterval(config['price_interval'])
        self.graph = config['graph'] if 'graph' in config else True
        self.check_member_variables(config_path)

    def check_member_variables(self, config_path: str):
        validate_type('symbol', self.symbol, str, config_path)
        if not self.symbol:
            raise NoSymbolsSpecifiedException(f"Please specify at least one symbol in: {config_path}")

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
        adapter.add_argument(Argument(ArgumentType.INTERVAL, self.price_interval))
        return adapter

    def create_fundamentals_adapter(self, symbol):
        adapter = self.new_adapter(symbol)
        value_types = [ValueType.SHARES]
        value_types += get_balance_sheet_value_types()
        value_types += get_earnings_value_types()
        value_types += get_income_value_types()
        value_types += get_cash_flow_value_types()
        # value_types += get_price_value_types()
        adapter.request_value_types = value_types
        # adapter.request_value_types = [
        #     ValueType.REVENUE,
        #     ValueType.CASH_FLOW,
        #     ValueType.EPS,
        #     ValueType.DIVIDENDS,
        #     ValueType.NET_INCOME,
        #     ValueType.ASSETS,
        #     ValueType.LIABILITIES,
        #     ValueType.SHARES,
        #     ValueType.DILUTED_SHARES,
        #     ValueType.EQUITY,
        # ]
        adapter.add_argument(Argument(ArgumentType.INTERVAL, self.fundamentals_interval))
        return adapter

    def new_adapter(self, symbol) -> Adapter:
        """
        Creates a new adapter with common configuration for the different IV use cases
        :param symbol: The symbol to create the adapter for
        :return: The created adapter
        """
        adapter = self.adapter_class(symbol, asset_type=None)
        adapter.base_symbol = self.base_symbol
        # end_date = datetime(year=2021, month=7, day=3)
        end_date = datetime.now()
        adapter.add_argument(Argument(ArgumentType.START_TIME, end_date - 10 * TimeInterval.YEAR.timedelta))
        adapter.add_argument(Argument(ArgumentType.END_TIME, end_date))
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

    def report_collections(self, locations: Locations, collections: Dict[str, AdapterCollection]) -> pandas.DataFrame:
        # A Collection can have multiple symbols tied to a variety of adapters, instead of iterating these right now,
        # we just support one, but if we want to do multiple then we can add support for it
        for name, collection in collections.items():
            eps_adapter = filter_adapters(collection.adapters, self.symbol, ValueType.EPS)
            eps_intervals: Set[TimeInterval] = set(
                [argument.value for argument in eps_adapter.arguments if argument.argument_type ==
                 ArgumentType.INTERVAL])
            assert len(eps_intervals) == 1, "Expected to report on 1 interval for {}, but found: {}".format(
                ValueType.EPS, eps_intervals)
            interval: TimeInterval = list(eps_intervals)[0]

            value_types = [ValueType.SHARES]
            value_types += get_balance_sheet_value_types()
            value_types += get_earnings_value_types()
            value_types += get_income_value_types()
            value_types += get_cash_flow_value_types()
            value_types += get_price_value_types()

            # last_time = collection.get_common_end_time()
            # first_time = collection.get_common_start_time()

            output_dir = locations.get_output_dir(Report.camel_to_snake(self.__class__.__name__))
            report_name = f"{self.get_run_name()}.log"
            report_path = os.path.join(output_dir, report_name)
            report: Report = Report(report_path)

            report.log('-- Start report for {}'.format(self.symbol))
            report.log('\n'.join(get_copyright_notice()))

            unbound_df: pandas.DataFrame = collection.get_columns(self.symbol, value_types)
            unbound_df.interpolate(method='time', inplace=True)
            first_time = get_common_start_time(unbound_df)
            last_time = get_common_end_time(unbound_df)
            report.log('Last time: {}  First time: {}'.format(last_time.strftime("%Y-%m-%d"),
                                                              first_time.strftime("%Y-%m-%d")))
            df: pandas.DataFrame = unbound_df.truncate(first_time, last_time)

            # get earnings data - we requested access to earnings info from IEX, but if not then we'll calculate it
            # e_df: pandas.DataFrame = df[get_earnings_value_types()]
            # e_df: pandas.DataFrame = collection.get_columns(self.symbol, earnings_value_types)

            # merge earnings data into the data - match earnings dates using +/- X weeks
            # df[ValueType.EPS] = ""
            # for date in df.index:
            #     closest_idx = e_df.index.get_loc(date, method='nearest')
            #     df.loc[date, ValueType.EPS] = e_df.iloc[closest_idx, :][ValueType.EPS]

            # use cash flow as the model for data - if something else makes more sense, then use it
            # cf_df = collection.get_columns(self.symbol, get_cash_flow_value_types())

            # merge cash flow data into the data - match earnings dates using +/- 2 weeks
            # df[ValueType.NET_INCOME] = ""
            # df[ValueType.DIVIDENDS] = ""
            # for date in df.index:
            #     closest_idx = cf_df.index.get_loc(date, method='nearest')
            #     df.loc[date, ValueType.NET_INCOME] = cf_df.iloc[closest_idx, :][ValueType.NET_INCOME]
            #     df.loc[date, ValueType.DIVIDENDS] = cf_df.iloc[closest_idx, :][ValueType.DIVIDENDS]

            # TODO: Where this is used, is it appropriate?
            outstanding_last_time = df[ValueType.SHARES].last_valid_index()
            outstanding = df.loc[outstanding_last_time, ValueType.SHARES]

            # # calculate the earnings info
            # # ETF, AAPL works fine here but GOOGL fails here, where does this get set? get_date(EARNINGS... is?
            # diluted = df.loc[last_time, ValueType.DILUTED_SHARES]
            # df[FundamentalRunner.CALCULATED_EPS] = ""
            # for date in df.index:
            #     net_income = df.loc[date, ValueType.NET_INCOME]
            #     # WARNING: For some like IEX we use netIncomeBasic which already has preferred stock removed
            #     #          in the section below this we removed common dividends which is wrong, we only remove
            #     #          preferred dividends to calculate EPS - because share holders don't have access to those
            #     df.loc[date, FundamentalRunner.CALCULATED_EPS] = net_income / diluted
            #     # df.loc[date, FundamentalRunner.CALCULATED_EPS] = net_income / outstanding
            #     # This was the wrong calculation:
            #     # future_dividends = df.loc[date, ValueType.DIVIDEND_PAYOUT]
            #     # df.loc[date, FundamentalRunner.CALCULATED_EPS] = (net_income - future_dividends) / outstanding
            #     # We only want to subtract _preferred_ dividends as shareholders don't get those, see this page:
            #     # https://www.fool.com/investing/stock-market/basics/earnings-per-share/#:~:text=EPS%20is%20calculated%20by%20subtracting,the%20number%20of%20shares%20outstanding.

            # get series data
            p_df = collection.get_columns(self.symbol, get_price_value_types())

            # merge series data into the data - match earnings dates using +/- 2 weeks
            df[ValueType.LOW] = ""
            df[ValueType.HIGH] = ""
            df[IntrinsicValueRunner.LOW_PE] = ""
            df[IntrinsicValueRunner.HIGH_PE] = ""
            for date in df.index:
                closest_idx = p_df.index.get_loc(date, method='nearest')
                # TODO: This only gets the closest (monthly) series entry and uses it's high and low, we could
                #       go through all of the months between the last and now to get a broader range of high/low
                #       since these dates are normally either quarterly or yearly
                df.loc[date, ValueType.LOW] = p_df.iloc[closest_idx, :][ValueType.LOW]
                df.loc[date, ValueType.HIGH] = p_df.iloc[closest_idx, :][ValueType.HIGH]
                df.loc[date, ValueType.CLOSE] = p_df.iloc[closest_idx, :][ValueType.CLOSE]
            multiple = 4 if self.fundamentals_interval is TimeInterval.QUARTER else 1
            df.loc[:, IntrinsicValueRunner.LOW_PE] = df.loc[:, ValueType.LOW] / (df.loc[:, ValueType.EPS] * multiple)
            df.loc[:, IntrinsicValueRunner.HIGH_PE] = df.loc[:, ValueType.HIGH] / (df.loc[:, ValueType.EPS] * multiple)
            pe_ratios = df.loc[:, IntrinsicValueRunner.LOW_PE] + df.loc[:, IntrinsicValueRunner.HIGH_PE]
            pe_ratios.dropna(inplace=True)

            #################################################################################
            # Report now...
            report_df = self.report_format(df)
            report_df[IntrinsicValueRunner.LOW_PE] = report_df[IntrinsicValueRunner.LOW_PE].apply(to_dollars)
            report_df[IntrinsicValueRunner.HIGH_PE] = report_df[IntrinsicValueRunner.HIGH_PE].apply(to_dollars)
            report.log("Data table for intrinsic value calculation using {}...\n{}".format(
                self.fundamentals_interval, report_df.to_string()))

            # predict into the future as far forwards as we have data backwards
            future_timedelta = df.index.max() - df.index.min()

            predictions = {}
            # last = {}
            future_time = last_time + future_timedelta
            for value_type in value_types:
                prediction = predict_value_type_linear(collection, self.symbol, value_type, future_time)
                predictions[value_type] = prediction
                # # values = symbol_handle.get_all_items(value_type)
                # # end_time = max(values.keys())
                # report.log("  - {}".format(value_type.as_title()))
                # # last[value_type] = df[last_time, value_type]
                # non_dollar_columns = [ValueType.SHARES]
                # current_last_time = df[value_type].last_valid_index()
                # current_value = df.loc[current_last_time, value_type]
                # current_value = f'{current_value:.2f}' if value_type in non_dollar_columns else to_dollars(
                #     current_value)
                # report.log("  Current    :  {} (on {})".format(current_value, current_last_time.strftime("%Y-%m-%d")))
                # prediction = f'{prediction:.2f}' if value_type in non_dollar_columns else to_dollars(prediction)
                # report.log("  Prediction :  {} (on {})".format(prediction, future_time.strftime("%Y-%m-%d")))

            predictions[IntrinsicValueRunner.LOW_PE] = predict_value_linear(df.loc[:, IntrinsicValueRunner.LOW_PE],
                                                                            future_time)
            predictions[IntrinsicValueRunner.HIGH_PE] = predict_value_linear(df.loc[:, IntrinsicValueRunner.HIGH_PE],
                                                                             future_time)

            predictions_df = pandas.DataFrame.from_dict([predictions])
            predictions_df[IntrinsicValueRunner.LOW_PE] = predictions_df[IntrinsicValueRunner.LOW_PE].apply(to_dollars)
            predictions_df[IntrinsicValueRunner.HIGH_PE] = predictions_df[IntrinsicValueRunner.HIGH_PE].apply(
                to_dollars)
            predictions_df.index = [future_time]
            # predictions_df.insert(0, "Date", [future_time])
            # predictions_df.set_index("Date")
            predictions_print = self.report_format(predictions_df)
            report.log("Data table of intrinsic value predictions using {}...\n{}".format(
                self.fundamentals_interval, predictions_print.to_string()))

            report.log("  - Book Value")
            assets_last_time = df[ValueType.ASSETS].last_valid_index()
            liabilities_last_time = df[ValueType.LIABILITIES].last_valid_index()
            book_value = df.loc[assets_last_time, ValueType.ASSETS] - df.loc[
                liabilities_last_time, ValueType.LIABILITIES]
            assert book_value != 0.0, "Total Assets {} - Total Liabilities {} = {} (book value should not be 0, " \
                                      "it will lead to a divide by zero problem for book value growth rate " \
                                      "calculations)".format(df.loc[assets_last_time, ValueType.ASSETS],
                                                             df.loc[liabilities_last_time, ValueType.LIABILITIES],
                                                             book_value)
            report.log("  Current    :  {} (on {})".format(to_dollars(book_value), last_time.strftime("%Y-%m-%d")))
            predicted_book_value = predictions[ValueType.ASSETS] - predictions[ValueType.LIABILITIES]
            report.log(
                "  Prediction :  {} (on {})".format(to_dollars(predicted_book_value), future_time.strftime("%Y-%m-%d")))

            report.log("  - Book Yield")
            # NOTE: we could do this math on the dataframe instead of scalar, but we don't currently need it
            eps_last_time = df[ValueType.EPS].last_valid_index()
            earnings_per_share = df.loc[eps_last_time, ValueType.EPS]
            dividend_last_time = df[ValueType.DIVIDENDS].last_valid_index()
            dividends_per_share = df.loc[dividend_last_time, ValueType.DIVIDENDS] / outstanding
            payout_ratio = dividends_per_share / earnings_per_share
            # On a per fundamentals_interval period, can be yearly, can be quarterly
            retention_ratio = 1 - payout_ratio
            book_value_per_share = book_value / outstanding
            book_yield_per_share = earnings_per_share / book_value_per_share
            book_value_growth = book_yield_per_share * retention_ratio

            # Predicted ROE - Using a trend-line equivalent predict where ROE will be
            # return_on_equity = predictions[ValueType.NET_INCOME] / predictions[ValueType.EQUITY]
            # Average ROE - If the last net income is negative, then using average will hopefully be positive...
            historic_roe = df.loc[:, ValueType.NET_INCOME] / df.loc[:, ValueType.EQUITY]
            return_on_equity = sum(historic_roe) / len(historic_roe)
            # Last ROE
            # shareholder_equity = df.loc[last_time, ValueType.EQUITY]
            # net_income = df.loc[last_time, ValueType.NET_INCOME]
            # return_on_equity = net_income / shareholder_equity

            calculated_book_values = {last_time: book_value_per_share}
            future_earnings = {}
            intervals = ceil((last_time - first_time) / interval.timedelta)
            for it in range(intervals):
                previous_date = it * interval.timedelta + last_time
                current_date = (1 + it) * interval.timedelta + last_time
                calculated_book_values[current_date] = calculated_book_values[previous_date] * (
                        1 + book_value_growth)
                value = calculated_book_values[current_date] * return_on_equity
                if not numpy.isnan(value):
                    future_earnings[current_date] = value

            report.log("  Dividend Payout        : {} (on {})".format(
                to_dollars(df.loc[last_time, ValueType.DIVIDENDS]),
                last_time.strftime("%Y-%m-%d")))
            report.log("  Dividends per Share    : ${:.2f}".format(dividends_per_share))
            report.log("  Payout Ratio           : {:.2f}%".format(payout_ratio * 100.0))
            report.log("  Retention Ratio        : {:.2f}%".format(retention_ratio * 100.0))
            report.log("  Book Yield per Share   : {:.2f}%".format(book_yield_per_share * 100.0))
            report.log("  Growth in Book Value   : {:.2f}%".format(book_value_growth * 100.0))
            report.log("  Return on Equity (ROE) : {:.2f}%".format(return_on_equity * 100.0))

            report.log("  - Estimate of Book Value per Share (using shares outstanding: {})".format(outstanding))
            report.log("  Current    : ${:.2f} (on {})".format(book_value_per_share, last_time.strftime("%Y-%m-%d")))
            final_date = max(list(calculated_book_values.keys()))
            report.log("  Calculated : ${:.2f} (on {})".format(calculated_book_values[final_date],
                                                               final_date.strftime("%Y-%m-%d")))

            report.log(
                f"  - Chart of future earnings\n{pandas.DataFrame.from_dict(future_earnings, orient='index', columns=['Future EPS'])}")
            report.log("  - Estimate of Earnings per Share")
            report.log("  Current    : ${:.2f} (on {})".format(earnings_per_share, last_time.strftime("%Y-%m-%d")))
            final_date = max(list(future_earnings.keys()))
            report.log("  Calculated : ${:.2f} (on {})".format(future_earnings[final_date],
                                                               final_date.strftime("%Y-%m-%d")))

            report.log("  - Historic P/E Ratios")
            max_pe = max(pe_ratios)
            avg_pe = sum(pe_ratios) / len(pe_ratios)
            median_pe = median(pe_ratios)
            min_pe = min(pe_ratios)
            report.log("  Max P/E: {:.2f}  Average P/E: {:.2f}  Median P/E: {:.2f}  Min P/E: {:.2f}  ".format(
                max_pe, avg_pe, median_pe, min_pe))

            # the predictions are from a linear regression and could be used, but instead we do as Buffet does:
            calculated_eps = future_earnings[final_date]  # predictions[ValueType.REPORTED_EPS]
            report.log("  - Future Share Price (historic P/E * future EPS ${}) - On {}".format(
                round(calculated_eps, 2), final_date.strftime("%Y-%m-%d")))
            max_price, avg_price, median_price, min_price = get_prices_from_earnings(
                calculated_eps, max_pe, median_pe, avg_pe, min_pe)
            report.log("  Max Price: {}  Average Price: {}  Median Price: {}  Min Price: {}".
                       format(to_dollars(max_price), to_dollars(avg_price),
                              to_dollars(median_price), to_dollars(min_price)))

            report.log("  - Future Return on Investment (ROI)")
            current_time = p_df.index.max()
            current_price_per_share = p_df.loc[current_time, ValueType.CLOSE]
            last_price = df.loc[last_time, ValueType.CLOSE]
            future_dividends = calculate_common_dividend(future_earnings, payout_ratio)
            report.log(report_common_dividends(future_dividends))
            report.log("  Last report price: {} ({})".format(to_dollars(last_price), last_time.strftime("%Y-%m-%d")))
            irr_last = report_irr(future_earnings, future_dividends, last_price,
                                  avg_price, max_price, median_price, min_price)
            report.log(
                "    Annual Rate of Return (IRR) - {} on {}".format(irr_last, final_date.strftime("%Y-%m-%d")))
            report.log("  Current price: {} ({})".format(to_dollars(current_price_per_share),
                                                         current_time.strftime("%Y-%m-%d")))
            irr_current = report_irr(future_earnings, future_dividends, current_price_per_share,
                                     avg_price, max_price, median_price, min_price)
            report.log(
                "    Annual Rate of Return (IRR) - {} on {}".format(irr_current, final_date.strftime("%Y-%m-%d")))

            report.log("  - Current Fair Share Price (historic P/E * current EPS ${}) - On {}".format(
                round(earnings_per_share, 2), current_time.strftime("%Y-%m-%d")))
            max_current, avg_current, median_current, min_current = get_prices_from_earnings(
                earnings_per_share, max_pe, median_pe, avg_pe, min_pe)
            report.log("  Max Price: {}  Average Price: {}  Median Price: {}  Min Price: {} ({:.2f}%)".
                       format(to_dollars(max_current), to_dollars(avg_current),
                              to_dollars(median_current), to_dollars(min_current),
                              (current_price_per_share / min_current * 100)))

            price_to_book_ratio = current_price_per_share / book_value_per_share
            report.log("  - Current price to book ratio: {:.2f}%".format(price_to_book_ratio * 100))

            short_debt_last_time = df[ValueType.SHORT_DEBT].last_valid_index()
            long_debt_last_time = df[ValueType.LONG_DEBT].last_valid_index()
            debt = df.loc[short_debt_last_time, ValueType.SHORT_DEBT] + df.loc[long_debt_last_time, ValueType.LONG_DEBT]
            debt_to_asset_ratio = debt / df.loc[assets_last_time, ValueType.ASSETS]
            report.log("  - Last report debt to asset ratio: {:.2f}%".format(debt_to_asset_ratio * 100))

            report.log('-- End report for {}'.format(self.symbol))
            logging.info(f'Report file: {file_link_format(report_path)}')

            return df

    def report_format(self, df):
        df_print = df.copy()
        df_print[ValueType.REVENUE] = df_print[ValueType.REVENUE].apply(to_dollars)
        df_print[ValueType.CASH_FLOW] = df_print[ValueType.CASH_FLOW].apply(to_dollars)
        df_print[ValueType.ASSETS] = df_print[ValueType.ASSETS].apply(to_dollars)
        df_print[ValueType.SHARES] = df_print[ValueType.SHARES].apply(to_abbrev)
        df_print[ValueType.LIABILITIES] = df_print[ValueType.LIABILITIES].apply(to_dollars)
        df_print[ValueType.LONG_DEBT] = df_print[ValueType.LONG_DEBT].apply(to_dollars)
        df_print[ValueType.SHORT_DEBT] = df_print[ValueType.SHORT_DEBT].apply(to_dollars)
        df_print[ValueType.EQUITY] = df_print[ValueType.EQUITY].apply(to_dollars)
        df_print[ValueType.EPS] = df_print[ValueType.EPS].apply(to_dollars)
        df_print[ValueType.NET_INCOME] = df_print[ValueType.NET_INCOME].apply(to_dollars)
        df_print[ValueType.DIVIDENDS] = df_print[ValueType.DIVIDENDS].apply(to_dollars)
        df_print[ValueType.HIGH] = df_print[ValueType.HIGH].apply(to_dollars)
        df_print[ValueType.LOW] = df_print[ValueType.LOW].apply(to_dollars)
        df_print[ValueType.CLOSE] = df_print[ValueType.CLOSE].apply(to_dollars)
        return df_print

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
