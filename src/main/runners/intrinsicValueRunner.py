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
import importlib
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Set

import numpy
import pandas
import yaml
from numpy import median
from sklearn import linear_model

from main.adapters.adapter import TimeInterval, AssetType
from main.adapters.adapterCollection import AdapterCollection
from main.adapters.argument import Argument, ArgumentType
from main.adapters.valueType import ValueType
from main.common.fileSystem import FileSystem
from main.common.report import Report
from main.executors.parallelExecutor import ParallelExecutor
from main.runners.runner import Runner
from main.visual.visualizer import Visualizer

# NOTE: This code automatically adds all modules in the thirdPartyShims directory
ext_adapter_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'adapters', 'thirdPartyShims'))
for module in os.listdir(ext_adapter_dir):
    if module == '__init__.py' or module[-3:] != '.py':
        continue
    importlib.import_module(f'.{module[:-3]}', f'main.adapters.thirdPartyShims')
del module


def to_dollars(value: float) -> str:
    abs_value = abs(value)
    if abs_value > 10000000000:
        value_as_str = "${:.1f}B".format(value / 1000000000)
    elif abs_value > 10000000:
        value_as_str = "${:.1f}M".format(value / 1000000)
    elif abs_value > 10000:
        value_as_str = "${:.1f}K".format(value / 1000)
    else:
        value_as_str = "${:.2f}".format(value)
    return value_as_str


class NoSymbolsSpecifiedException(RuntimeError):
    pass


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


class IntrinsicValueRunner(Runner):
    HIGH_PE: str = 'High P/E'
    LOW_PE: str = 'Low P/E'


    symbols: List[str]
    base_symbol: str

    def __init__(self, config_path):
        super().__init__()
        self.symbols = []
        self.adapter_class = None
        self.base_symbol = 'USD'
        self.read_config_file(config_path)

    # @staticmethod
    # def get_config_file() -> str:
    #     return IntrinsicValueRunner.config_path

    def start(self):
        logging.info("#### Starting intrinsic value runner...")
        success = True

        # Multiple collections == Multiple plots : Each collection is in it's own dict entry under the query type
        # collections = self.multiple_collections(symbols, overrides, base_symbol, adapter_class, interval, today)
        # Single collection == Single plots      : There is one collection in the dict with the key Fundamentals
        collections: Dict[str, AdapterCollection] = self.single_collection(self.symbols)

        self.report_collections(collections)

        # draw = True
        # draw = False
        # if draw:
        #     self.plot_collections(collections,  configuration.query_argument[QueryArgument.BALANCE_SHEET_INTERVAL])

        self.write_config()

        return success

    def write_config(self):
        pass

    def read_config_file(self, config_path):
        with open(config_path) as f:
            config = yaml.full_load(f)
            self.symbols = config['symbols']
            if not self.symbols:
                raise NoSymbolsSpecifiedException(f"Please specify at least one symbol in: {config_path}")
            class_name = config['adapter_class']
            self.adapter_class = getattr(sys.modules[f'main.adapters.thirdPartyShims.{class_name[0].lower()}{class_name[1:]}'], f'{class_name}')
            # self.adapter_class = getattr(sys.modules[__name__], class_name)
            self.base_symbol = config['base_symbol']

    def single_collection(self, symbols: List[str]) -> Dict[str, AdapterCollection]:
        collection: AdapterCollection = AdapterCollection()
        for symbol in symbols:
            collection.add(self.create_price_adapter(symbol))
            collection.add(self.create_fundamentals_adapter(symbol))
        # collection.set_all_cache_key_dates(datetime(year=2021, month=6, day=25))
        collection.retrieve_all_data()
        return {'Fundamentals': collection}

    def create_price_adapter(self, symbol):
        adapter = self.new_adapter(symbol)
        adapter.value_types = [
            ValueType.HIGH,
            ValueType.OPEN,
            ValueType.CLOSE,
            ValueType.LOW,
        ]
        adapter.add_argument(Argument(ArgumentType.INTERVAL, TimeInterval.WEEK))
        return adapter

    def create_fundamentals_adapter(self, symbol):
        adapter = self.new_adapter(symbol)
        adapter.value_types = [
            ValueType.EPS,
            ValueType.DIVIDENDS,
            ValueType.NET_INCOME,
            ValueType.ASSETS,
            ValueType.LIABILITIES,
            ValueType.OUTSTANDING_SHARES,
            ValueType.DILUTED_SHARES,
            ValueType.SHAREHOLDER_EQUITY,
        ]
        adapter.add_argument(Argument(ArgumentType.INTERVAL, TimeInterval.YEAR))
        # adapter.add_argument(Argument(ArgumentType.INTERVAL, TimeInterval.QUARTER))
        return adapter

    def new_adapter(self, symbol):
        adapter = self.adapter_class(symbol, asset_type=None)
        adapter.base_symbol = self.base_symbol
        end_date = datetime(year=2021, month=7, day=3)  # datetime.now()
        adapter.add_argument(Argument(ArgumentType.START_TIME, end_date - 10 * TimeInterval.YEAR.timedelta))
        adapter.add_argument(Argument(ArgumentType.END_TIME, end_date))
        adapter.cache_key_date = end_date
        asset_type_overrides = {
            'ETH': AssetType.DIGITAL_CURRENCY,
            'LTC': AssetType.DIGITAL_CURRENCY,
            'GEO': AssetType.EQUITY,
            'BLK': AssetType.EQUITY,
        }
        adapter.asset_type = asset_type_overrides[symbol] if symbol in asset_type_overrides else None
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

    def report_collections(self, collections: Dict[str, AdapterCollection]):
        # A Collection can have multiple symbols tied to a variety of adapters, instead of iterating these right now,
        # we just support one, but if we want to do multiple then we can add support for it
        for name, collection in collections.items():
            symbols: Set[str] = set([adapter.symbol for adapter in collection.adapters])
            assert len(symbols) == 1, "Expected to report on 1 symbol, but found: {}".format(list(symbols))
            symbol = list(symbols)[0]

            eps_adapter = collection.get_adapter(symbol, ValueType.EPS)
            eps_intervals: Set[TimeInterval] = set(
                [argument.value for argument in eps_adapter.arguments if argument.argument_type ==
                 ArgumentType.INTERVAL])
            assert len(eps_intervals) == 1, "Expected to report on 1 interval for {}, but found: {}".format(
                ValueType.EPS, eps_intervals)
            interval: TimeInterval = list(eps_intervals)[0]

            # use balance sheet as the model for data - if something else makes more sense, then use it
            value_types = [
                ValueType.ASSETS,
                ValueType.LIABILITIES,
                ValueType.OUTSTANDING_SHARES,
                ValueType.SHAREHOLDER_EQUITY,
            ]
            earnings_value_types = [ValueType.EPS]
            value_types += earnings_value_types
            cash_flow_value_types = [ValueType.NET_INCOME, ValueType.DIVIDENDS]
            value_types += cash_flow_value_types
            price_value_types = [ValueType.HIGH, ValueType.LOW, ValueType.CLOSE]
            value_types += price_value_types

            last_time = collection.get_common_end_time()
            first_time = collection.get_common_start_time()

            output_dir = FileSystem.get_output_dir(Report.camel_to_snake(self.__class__.__name__))
            report_name = f"{symbol}_{last_time.strftime('%Y-%m-%d')}_{self.adapter_class.__name__}.log"
            report_path = os.path.join(output_dir, report_name)
            report: Report = Report(report_path)

            report.log('-- Start report for {}'.format(symbol))
            report.log('Last time: {}  First time: {}'.format(last_time.strftime("%Y-%m-%d"),
                                                              first_time.strftime("%Y-%m-%d")))

            unbound_df: pandas.DataFrame = collection.get_columns(symbol, value_types)

            # NOTE: In the future we can add an interpolation that will either fill nan values with the previous or
            #       we can do some kind of linear interpolation between data points to fill nans, but with boundaries
            #       known and filling middle nans we should end up with a complete data set...
            df: pandas.DataFrame = unbound_df.truncate(first_time, last_time)

            # get earnings data - we requested access to earnings info from IEX, but if not then we'll calculate it
            e_df: pandas.DataFrame = collection.get_columns(symbol, earnings_value_types)

            # merge earnings data into the data - match earnings dates using +/- X weeks
            df[ValueType.EPS] = ""
            for date in df.index:
                closest_idx = e_df.index.get_loc(date, method='nearest')
                df.loc[date, ValueType.EPS] = e_df.iloc[closest_idx, :][ValueType.EPS]

            # use cash flow as the model for data - if something else makes more sense, then use it
            cf_df = collection.get_columns(symbol, cash_flow_value_types)

            # merge cash flow data into the data - match earnings dates using +/- 2 weeks
            df[ValueType.NET_INCOME] = ""
            df[ValueType.DIVIDENDS] = ""
            for date in df.index:
                closest_idx = cf_df.index.get_loc(date, method='nearest')
                df.loc[date, ValueType.NET_INCOME] = cf_df.iloc[closest_idx, :][ValueType.NET_INCOME]
                df.loc[date, ValueType.DIVIDENDS] = cf_df.iloc[closest_idx, :][ValueType.DIVIDENDS]

            # TODO: Where this is used, is it appropriate?
            outstanding = df.loc[last_time, ValueType.OUTSTANDING_SHARES]

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
            p_df = collection.get_columns(symbol, price_value_types)

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
            df.loc[:, IntrinsicValueRunner.LOW_PE] = df.loc[:, ValueType.LOW] / df.loc[:, ValueType.EPS]
            df.loc[:, IntrinsicValueRunner.HIGH_PE] = df.loc[:, ValueType.HIGH] / df.loc[:, ValueType.EPS]
            pe_ratios = df.loc[:, IntrinsicValueRunner.LOW_PE] + df.loc[:, IntrinsicValueRunner.HIGH_PE]

            #################################################################################
            # Report now...
            df_print = df.copy()
            df_print[ValueType.ASSETS] = df_print[ValueType.ASSETS].apply(to_dollars)
            df_print[ValueType.LIABILITIES] = df_print[ValueType.LIABILITIES].apply(to_dollars)
            df_print[ValueType.SHAREHOLDER_EQUITY] = df_print[ValueType.SHAREHOLDER_EQUITY].apply(to_dollars)
            df_print[ValueType.EPS] = df_print[ValueType.EPS].apply(to_dollars)
            df_print[ValueType.NET_INCOME] = df_print[ValueType.NET_INCOME].apply(to_dollars)
            df_print[ValueType.DIVIDENDS] = df_print[ValueType.DIVIDENDS].apply(to_dollars)
            df_print[ValueType.HIGH] = df_print[ValueType.HIGH].apply(to_dollars)
            df_print[ValueType.LOW] = df_print[ValueType.LOW].apply(to_dollars)
            df_print[ValueType.CLOSE] = df_print[ValueType.CLOSE].apply(to_dollars)
            df_print[IntrinsicValueRunner.LOW_PE] = df_print[IntrinsicValueRunner.LOW_PE].apply(to_dollars)
            df_print[IntrinsicValueRunner.HIGH_PE] = df_print[IntrinsicValueRunner.HIGH_PE].apply(to_dollars)
            report.log("Data frame contents for intrinsic value...\n{}".format(df_print.to_string()))

            # predict into the future as far forwards as we have data backwards
            intervals = len(df.index)
            future_timedelta = intervals * interval.timedelta

            predictions = {}
            # last = {}
            future_time = last_time + future_timedelta
            for value_type in value_types:
                prediction = IntrinsicValueRunner.predict_future_value_linear(symbol, future_time, collection,
                                                                              value_type)
                predictions[value_type] = prediction
                # values = symbol_handle.get_all_items(value_type)
                # end_time = max(values.keys())
                report.log("  - {}".format(value_type.as_title()))
                # last[value_type] = df[last_time, value_type]
                non_dollar_columns = [ValueType.OUTSTANDING_SHARES]
                current_value = df.loc[last_time, value_type]
                current_value = f'{current_value:.2f}' if value_type in non_dollar_columns else to_dollars(current_value)
                report.log("  Current    :  {} (on {})".format(current_value, last_time.strftime("%Y-%m-%d")))
                prediction = f'{prediction:.2f}' if value_type in non_dollar_columns else to_dollars(prediction)
                report.log("  Prediction :  {} (on {})".format(prediction, future_time.strftime("%Y-%m-%d")))

            report.log("  - Book Value")
            book_value = df.loc[last_time, ValueType.ASSETS] - df.loc[last_time, ValueType.LIABILITIES]
            assert book_value != 0.0, "Total Assets {} - Total Liabilities {} = {} (book value should not be 0)".format(
                df.loc[last_time, ValueType.ASSETS], df.loc[last_time, ValueType.LIABILITIES], book_value)
            report.log("  Current    : ${:.2f} (on {})".format(book_value, last_time.strftime("%Y-%m-%d")))
            predicted_book_value = predictions[ValueType.ASSETS] - predictions[ValueType.LIABILITIES]
            report.log(
                "  Prediction : ${:.2f} (on {})".format(predicted_book_value, future_time.strftime("%Y-%m-%d")))

            report.log("  - Book Yield")
            # NOTE: we could do this math on the dataframe instead of scalar, but we don't currently need it
            earnings_per_share = df.loc[last_time, ValueType.EPS]
            dividends_per_share = df.loc[last_time, ValueType.DIVIDENDS] / outstanding
            payout_ratio = dividends_per_share / earnings_per_share
            retention_ratio = 1 - payout_ratio
            book_value_per_share = book_value / outstanding
            book_yield_per_share = earnings_per_share / book_value_per_share
            book_value_growth = book_yield_per_share * retention_ratio

            # Predicted ROE - Using a trend-line equivalent predict where ROW will be
            return_on_equity = predictions[ValueType.NET_INCOME] / predictions[ValueType.SHAREHOLDER_EQUITY]
            # Average ROE - If the last net income is negative, then using average will hopefully be positive...
            # historic_roe = df.loc[:, ValueType.NET_INCOME] / df.loc[:, ValueType.TOTAL_SHAREHOLDER_EQUITY]
            # return_on_equity = sum(historic_roe) / len(historic_roe)
            # Last ROE
            # shareholder_equity = df.loc[last_time, ValueType.TOTAL_SHAREHOLDER_EQUITY]
            # net_income = df.loc[last_time, ValueType.NET_INCOME]
            # return_on_equity = net_income / shareholder_equity

            calculated_book_values = {last_time: book_value_per_share}
            future_earnings = {}
            for it in range(intervals):
                previous_date = it * interval.timedelta + last_time
                current_date = (1 + it) * interval.timedelta + last_time
                calculated_book_values[current_date] = calculated_book_values[previous_date] * (
                        1 + book_value_growth)
                future_earnings[current_date] = calculated_book_values[current_date] * return_on_equity

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

            report.log("  - Estimate of Earnings per Share")
            report.log("  Current    : ${:.2f} (on {})".format(earnings_per_share, last_time.strftime("%Y-%m-%d")))
            final_date = max(list(future_earnings.keys()))
            report.log("  Calculated : ${:.2f} (on {})".format(future_earnings[final_date],
                                                               final_date.strftime("%Y-%m-%d")))

            report.log("  - Future P/E (using historic P/E ratios)")
            max_pe = max(pe_ratios)
            avg_pe = sum(pe_ratios) / len(pe_ratios)
            median_pe = median(pe_ratios)
            min_pe = min(pe_ratios)
            report.log("  Max P/E: {:.2f}  Average P/E: {:.2f}  Median P/E: {:.2f}  Min P/E: {:.2f}  ".format(
                max_pe, avg_pe, median_pe, min_pe))

            # the predictions are from a linear regression and could be used, but instead we do as Buffet does:
            calculated_eps = future_earnings[final_date]  # predictions[ValueType.REPORTED_EPS]
            report.log("  - Future Share Price (future P/E * future EPS ${})".format(round(calculated_eps, 2)))
            max_price = max_pe * calculated_eps
            max_price = -1.0 * max_price if (max_pe < 0) and (calculated_eps < 0) else max_price
            avg_price = avg_pe * calculated_eps
            avg_price = -1.0 * avg_price if (avg_pe < 0) and (calculated_eps < 0) else avg_price
            median_price = median_pe * calculated_eps
            median_price = -1.0 * median_price if (median_pe < 0) and (calculated_eps < 0) else median_price
            min_price = min_pe * calculated_eps
            min_price = -1.0 * min_price if (min_pe < 0) and (calculated_eps < 0) else min_price
            report.log("  Max Price: {}  Average Price: {}  Median Price: {}  Min Price: {}".
                       format(to_dollars(max_price), to_dollars(avg_price),
                              to_dollars(median_price), to_dollars(min_price)))

            report.log("  - Future Return on Investment (ROI)")
            current_time = p_df.index.max()
            current_price = p_df.loc[current_time, ValueType.CLOSE]
            last_price = df.loc[last_time, ValueType.CLOSE]
            future_dividends = calculate_common_dividend(future_earnings, payout_ratio)
            report.log(report_common_dividends(future_dividends))
            report.log("  Last report price: {} ({})".format(to_dollars(last_price), last_time.strftime("%Y-%m-%d")))
            irr_last = report_irr(future_earnings, future_dividends, last_price,
                                  avg_price, max_price, median_price, min_price)
            report.log(
                "    Annual Rate of Return (IRR) - {} on {}".format(irr_last, final_date.strftime("%Y-%m-%d")))
            report.log("  Current price: {} ({})".format(to_dollars(current_price), current_time.strftime("%Y-%m-%d")))
            irr_current = report_irr(future_earnings, future_dividends, current_price,
                                     avg_price, max_price, median_price, min_price)
            report.log(
                "    Annual Rate of Return (IRR) - {} on {}".format(irr_current, final_date.strftime("%Y-%m-%d")))
            report.log('-- End report for {}'.format(symbol))

    # @staticmethod
    # def get_data(adapter: Adapter) -> pandas.DataFrame:  # , value_types):
    #     df = adapter.data
    #     # flat_data, columns = adapter.get_all_data_flat()
    #     # df = pandas.DataFrame.from_dict(flat_data, orient='index', columns=columns)
    #     # df.index.name = 'Date'
    #     first_date = df.index[-1]
    #     df[FundamentalRunner.DAYS_FROM_START] = (df.index - first_date).days
    #     return df

    @staticmethod
    def predict_future_value_linear(symbol: str, future_time: datetime, collection: AdapterCollection,
                                    value_type: ValueType):
        adapter = collection.get_adapter(symbol, value_type)
        start_time = adapter.get_common_start_time()
        end_time = adapter.get_common_end_time()
        column: pandas.Series = adapter.get_column_between(start_time, end_time, value_type)
        column = column.sort_index(ascending=True)
        y = column.values
        days_from_start = (column.index - start_time).days.to_numpy()
        x = days_from_start.reshape(-1, 1)
        model = linear_model.LinearRegression().fit(x, y)
        future_days = (future_time - start_time).days
        predictions = model.predict([[future_days]])
        # logging.info(df)
        return predictions[0]

    def plot_collections(self, collections, interval):
        visual_date_dir = FileSystem.get_and_clean_timestamp_dir(FileSystem.get_cache_dir('visuals'))
        # executor = SequentialExecutor(visual_date_dir)
        executor = ParallelExecutor(visual_date_dir)
        for name, collection in collections.items():
            title = "{} {}".format(list(collection.symbol_handles.keys())[0], self.get_title_string(interval, name))
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

