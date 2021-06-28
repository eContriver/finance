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
import math
import os
from datetime import timedelta, datetime
from enum import Enum
from typing import Dict, List, Set

import numpy
import pandas
from numpy import median
from sklearn import linear_model

from main.adapters.adapter import TimeInterval, Adapter, AssetType
from main.adapters.valueType import ValueType
from main.adapters.argument import Argument, ArgumentType
from main.adapters.thirdPartyShims.alphaVantage import AlphaVantage
from main.adapters.thirdPartyShims.iexCloud import IexCloud
from main.common.fileSystem import FileSystem
from main.executors.parallelExecutor import ParallelExecutor
from main.adapters.adapterCollection import AdapterCollection
from main.runners.runner import Runner
from main.visual.visualizer import Visualizer


class FundamentalRunner(Runner):
    # DAYS_FROM_START = 'Days'
    HIGH_PE = 'High P/E'
    LOW_PE = 'Low P/E'
    CALCULATED_EPS = 'Calculated EPS'

    def __init__(self):
        super().__init__()

    def start(self):
        logging.info("#### Starting discounted cash flow (DCF) runner...")
        success = True

        symbols = [
            # 'NVDA'  # Annual Expected Rate of Return (IRR) - Max: 29.233%  Average: 22.1999%  Median: 22.7916%  Min: 11.9359% on 2031-01-19
            'XLNX'
            # 'TTCF'
            # TTCF does not return any cash flow data using IEX, and it fails
            # 'BRK-A'  # A++ < AlphaVantage has some serious problems with share count here
            # 'TSLA'  # D <- the numbers are trending in the right way
            # 'AAPL'  # C
            # 'GOOG'  # A
            # 'GOOGL'  # A < Needed for IEX to get income
            # 'COST'  # Annual Expected Rate of Return (IRR) - Max: 34.7726%  Average: 28.9067%  Median: 25.7128%  Min: 21.5404% on 2030-08-18
            # 'DIS'   # Annual Expected Rate of Return (IRR) - Max: 21.5303%  Average: 11.2693%  Median: 10.5447%  Min: 0.0% on 2030-09-21
            # DIS only get 3y balance sheet and 2y earnings from AlphaVantage for some reason
            # 'NKE'
            # 'NFLX'
            # 'DE'  # Max: 16.5115%  Average: 12.1755%  Median: 12.3128%  Min: 5.3439% on 2025-10-26
            # 'PLUG' # Not expected to be profitable until

            #### Michael Burry sold
            # 'LILA'  # shareholder equity dropped 20% in last 3 years (2017-12-31)
            # 'PDS'  # showed negative, for earnings, we're disabling calculated_eps but first switch to iex
            # 'ROIC'
            # 'MO'
            # 'CVS'
            # 'TCOM'
            # 'QRVO'
            # 'FB'
            # 'GME'
            # 'MSGN'
            # 'DISCA'
            # 'WDC'
            # 'QREA'
            # 'UNIT'
            # 'RPT'
            # 'DBI'
            # 'ALL'
            # 'KBAL'
            #### Michael Burry bought
            # 'ARCC'  # looks good
            # 'SXC'  # assets going down and shareholder equity
            # 'IMKTA'  # A++ very attractive, last quarter was questionable, perhaps we need to verify it
            # 'HFC' # I don't see it, maybe try yearly
            # 'CXW'  # wow, why is this on sale?
            # 'TAP'  # lost $900M this last year!
            # 'GEO'  # not looking good
            # 'WFC'  # more risk than reward
            # 'DNOW' # losing money and not progresing
            # 'LUMN'  # negative net income which just turned around
            # 'UBA'  # not great but price just dropped a lot
        ]

        # Multiple collections == Multiple plots : Each collection is in it's own dict entry under the query type
        # collections = self.multiple_collections(symbols, overrides, base_symbol, adapter_class, interval, today)
        # Single collection == Single plots      : There is one collection in the dict with the key Fundamentals
        collections: Dict[str, AdapterCollection] = self.single_collection(symbols)

        self.report_collections(collections)

        # draw = True
        # draw = False
        # if draw:
        #     self.plot_collections(collections, configuration.query_argument[QueryArgument.BALANCE_SHEET_INTERVAL])

        return success

    def single_collection(self, symbols: List[str]) -> Dict[str, AdapterCollection]:
        collection: AdapterCollection = AdapterCollection()
        for symbol in symbols:
            collection.add(self.create_price_adapter(symbol))
            collection.add(self.create_fundamentals_adapter(symbol))
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
            ValueType.REPORTED_EPS,
            # ValueType.ESTIMATED_EPS,
            # ValueType.SURPRISE_EPS,
            # ValueType.SURPRISE_PERCENTAGE_EPS,
            # ValueType.GROSS_PROFIT,
            # ValueType.TOTAL_REVENUE,
            # ValueType.OPERATING_CASH_FLOW,
            ValueType.DIVIDEND_PAYOUT,
            ValueType.NET_INCOME,
            ValueType.TOTAL_ASSETS,
            ValueType.TOTAL_LIABILITIES,
            ValueType.OUTSTANDING_SHARES,
            ValueType.DILUTED_SHARES,
            ValueType.TOTAL_SHAREHOLDER_EQUITY,
        ]
        adapter.add_argument(Argument(ArgumentType.INTERVAL, TimeInterval.YEAR))
        # adapter.add_argument(Argument(ArgumentType.INTERVAL, TimeInterval.QUARTER)) # TODO: Fix IEX w/ this
        return adapter

    def new_adapter(self, symbol):
        # adapter_class = Sec
        adapter_class = IexCloud
        # adapter_class = AlphaVantage
        adapter = adapter_class(symbol, asset_type=None)
        adapter.base_symbol = 'USD'
        end_date = datetime(year=2021, month=6, day=3)
        adapter.add_argument(Argument(ArgumentType.START_TIME, end_date - 10 * TimeInterval.YEAR.timedelta))
        adapter.add_argument(Argument(ArgumentType.END_TIME, end_date))
        adapter.cache_key_date = end_date
        # adapter.cache_key_date = None
        asset_type_overrides = {
            'ETH': AssetType.DIGITAL_CURRENCY,
            'LTC': AssetType.DIGITAL_CURRENCY,
            'GEO': AssetType.EQUITY,
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
    #
    @staticmethod
    def report_collections(collections: Dict[str, AdapterCollection]):
        for name, collection in collections.items():
            symbols: Set[str] = set([adapter.symbol for adapter in collection.adapters])
            assert len(symbols) == 1, "Expected to report on 1 symbol, but found: {}".format(symbols)
            symbol = list(symbols)[0]
            logging.info('Report for {}'.format(symbol))

            eps_adapter = collection.get_adapter(symbol, ValueType.REPORTED_EPS)
            eps_intervals: Set[TimeInterval] = set(
                [argument.value for argument in eps_adapter.arguments if argument.argument_type ==
                 ArgumentType.INTERVAL])
            assert len(eps_intervals) == 1, "Expected to report on 1 interval for {}, but found: {}".format(
                ValueType.REPORTED_EPS, eps_intervals)
            interval: TimeInterval = list(eps_intervals)[0]

            # use balance sheet as the model for data - if something else makes more sense, then use it
            value_types = [
                ValueType.TOTAL_ASSETS,
                ValueType.TOTAL_LIABILITIES,
                ValueType.OUTSTANDING_SHARES,
                ValueType.DILUTED_SHARES,
                ValueType.TOTAL_SHAREHOLDER_EQUITY,
            ]
            earnings_value_types = [ValueType.REPORTED_EPS]
            value_types += earnings_value_types
            cash_flow_value_types = [ValueType.NET_INCOME, ValueType.DIVIDEND_PAYOUT]
            value_types += cash_flow_value_types
            price_value_types = [ValueType.HIGH, ValueType.LOW, ValueType.CLOSE]
            value_types += price_value_types

            last_time = collection.get_common_end_time()
            first_time = collection.get_common_start_time()
            logging.info('Last time: {}  First time: {}'.format(last_time.strftime("%Y-%m-%d"),
                                                                first_time.strftime("%Y-%m-%d")))

            unbound_df: pandas.DataFrame = collection.get_columns(symbol, value_types)

            # NOTE: In the future we can add an interpolation that will either fill nan values with the previous or
            #       we can do some kind of linear interpolation between data points to fill nans, but with boundaries
            #       known and filling middle nans we should end up with a complete data set...
            df: pandas.DataFrame = unbound_df.truncate(first_time, last_time)

            # get earnings data - we requested access to earnings info from IEX, but if not then we'll calculate it
            e_df: pandas.DataFrame = collection.get_columns(symbol, earnings_value_types)

            # merge earnings data into the data - match earnings dates using +/- X weeks
            df[ValueType.REPORTED_EPS] = ""
            for date in df.index:
                closest_idx = e_df.index.get_loc(date, method='nearest')
                df.loc[date, ValueType.REPORTED_EPS] = e_df.iloc[closest_idx, :][ValueType.REPORTED_EPS]
                # for current_date in e_df.index:
                #     df.loc[date, ValueType.REPORTED_EPS] = e_df.get_loc(current_date, method='nearest')
                #     delta = abs(date - current_date)
                #     if delta < timedelta(weeks=5):
                #         df.loc[date, ValueType.REPORTED_EPS] = e_df.loc[current_date, ValueType.REPORTED_EPS]
                #         break

            # use cash flow as the model for data - if something else makes more sense, then use it
            cf_df = collection.get_columns(symbol, cash_flow_value_types)

            # merge cash flow data into the data - match earnings dates using +/- 2 weeks
            df[ValueType.NET_INCOME] = ""
            df[ValueType.DIVIDEND_PAYOUT] = ""
            for date in df.index:
                closest_idx = cf_df.index.get_loc(date, method='nearest')
                df.loc[date, ValueType.NET_INCOME] = cf_df.iloc[closest_idx, :][ValueType.NET_INCOME]
                df.loc[date, ValueType.DIVIDEND_PAYOUT] = cf_df.iloc[closest_idx, :][ValueType.DIVIDEND_PAYOUT]
                # for current_date in cf_df.index:
                #     delta = abs(date - current_date)
                #     if delta < timedelta(weeks=8):
                #         df.loc[date, ValueType.NET_INCOME] = cf_df.loc[current_date, ValueType.NET_INCOME]
                #         df.loc[date, ValueType.DIVIDEND_PAYOUT] = cf_df.loc[current_date, ValueType.DIVIDEND_PAYOUT]
                #         break

            # TODO: Where this is used, is it appropriate?
            outstanding = df.loc[last_time, ValueType.OUTSTANDING_SHARES]

            # calculate the earnings info
            # ETF, AAPL works fine here but GOOGL fails here, where does this get set? get_date(EARNINGS... is?
            diluted = df.loc[last_time, ValueType.DILUTED_SHARES]
            df[FundamentalRunner.CALCULATED_EPS] = ""
            for date in df.index:
                net_income = df.loc[date, ValueType.NET_INCOME]
                # WARNING: For some like IEX we use netIncomeBasic which already has preferred stock removed
                #          in the section below this we removed common dividends which is wrong, we only remove
                #          preferred dividends to calculate EPS - because share holders don't have access to those
                df.loc[date, FundamentalRunner.CALCULATED_EPS] = net_income / diluted
                # df.loc[date, FundamentalRunner.CALCULATED_EPS] = net_income / outstanding
                # This was the wrong calculation:
                # common_dividends = df.loc[date, ValueType.DIVIDEND_PAYOUT]
                # df.loc[date, FundamentalRunner.CALCULATED_EPS] = (net_income - common_dividends) / outstanding
                # We only want to subtract _preferred_ dividends as shareholders don't get those, see this page:
                # https://www.fool.com/investing/stock-market/basics/earnings-per-share/#:~:text=EPS%20is%20calculated%20by%20subtracting,the%20number%20of%20shares%20outstanding.

            # get series data
            p_df = collection.get_columns(symbol, price_value_types)

            # merge series data into the data - match earnings dates using +/- 2 weeks
            df[ValueType.LOW] = ""
            df[ValueType.HIGH] = ""
            df[FundamentalRunner.LOW_PE] = ""
            df[FundamentalRunner.HIGH_PE] = ""
            for date in df.index:
                closest_idx = p_df.index.get_loc(date, method='nearest')
                # TODO: This only gets the closest (monthly) series entry and uses it's high and low, we could
                #       go through all of the months between the last and now to get a broader range of high/low
                #       sicne these dates are normally either quarterly or yearly
                df.loc[date, ValueType.LOW] = p_df.iloc[closest_idx, :][ValueType.LOW]
                df.loc[date, ValueType.HIGH] = p_df.iloc[closest_idx, :][ValueType.HIGH]
                df.loc[date, ValueType.CLOSE] = p_df.iloc[closest_idx, :][ValueType.CLOSE]
            df.loc[:, FundamentalRunner.LOW_PE] = df.loc[:, ValueType.LOW] / df.loc[:, ValueType.REPORTED_EPS]
            df.loc[:, FundamentalRunner.HIGH_PE] = df.loc[:, ValueType.HIGH] / df.loc[:, ValueType.REPORTED_EPS]
            pe_ratios = df.loc[:, FundamentalRunner.LOW_PE] + df.loc[:, FundamentalRunner.HIGH_PE]

            #################################################################################
            # Report now...
            logging.info("Data frame contents for discounted cash flow modeling...\n{}".format(df.to_string()))

            # predict into the future as far forwards as we have data backwards
            intervals = len(df.index)
            future_timedelta = intervals * interval.timedelta

            predictions = {}
            # last = {}
            future_time = last_time + future_timedelta
            for value_type in value_types:
                # predictions
                prediction = FundamentalRunner.predict_future_value_linear(symbol, future_time, collection, value_type)
                predictions[value_type] = prediction
                # values = symbol_handle.get_all_items(value_type)
                # end_time = max(values.keys())
                logging.info("  - {}".format(value_type.as_title()))
                # last[value_type] = df[last_time, value_type]
                logging.info("  Current    :  {:.2f} (on {})".format(df.loc[last_time, value_type],
                                                                     last_time.strftime("%Y-%m-%d")))
                logging.info("  Prediction :  {:.2f} (on {})".format(prediction, future_time.strftime("%Y-%m-%d")))

            logging.info("  - Book Value")
            book_value = df.loc[last_time, ValueType.TOTAL_ASSETS] - df.loc[last_time, ValueType.TOTAL_LIABILITIES]
            assert book_value != 0.0, "Total Assets {} - Total Liabilities {} = {} (book value should not be 0)".format(
                df.loc[last_time, ValueType.TOTAL_ASSETS], df.loc[last_time, ValueType.TOTAL_LIABILITIES], book_value)
            logging.info("  Current    : ${:.2f} (on {})".format(book_value, last_time.strftime("%Y-%m-%d")))
            predicted_book_value = predictions[ValueType.TOTAL_ASSETS] - predictions[ValueType.TOTAL_LIABILITIES]
            logging.info(
                "  Prediction : ${:.2f} (on {})".format(predicted_book_value, future_time.strftime("%Y-%m-%d")))

            logging.info("  - Book Yield")
            # NOTE: we could do this math on the dataframe instead of scalar, but we don't currently need it
            earnings_per_share = df.loc[last_time, ValueType.REPORTED_EPS]
            dividends_per_share = df.loc[last_time, ValueType.DIVIDEND_PAYOUT] / outstanding
            payout_ratio = dividends_per_share / earnings_per_share
            retention_ratio = 1 - payout_ratio
            book_value_per_share = book_value / outstanding
            book_yield_per_share = earnings_per_share / book_value_per_share
            book_value_growth = book_yield_per_share * retention_ratio

            # Average ROE - If the last net income is negative, then using average will hopefully be positive...
            historic_roe = df.loc[:, ValueType.NET_INCOME] / df.loc[:, ValueType.TOTAL_SHAREHOLDER_EQUITY]
            return_on_equity = sum(historic_roe) / len(historic_roe)
            # Last ROE
            # shareholder_equity = df.loc[last_time, ValueType.TOTAL_SHAREHOLDER_EQUITY]
            # net_income = df.loc[last_time, ValueType.NET_INCOME]
            # return_on_equity = net_income / shareholder_equity

            calculated_book_values = {last_time: book_value_per_share}
            calculated_earnings = {}
            for it in range(intervals):
                previous_date = it * interval.timedelta + last_time
                current_date = (1 + it) * interval.timedelta + last_time
                calculated_book_values[current_date] = calculated_book_values[previous_date] * (
                        1 + book_value_growth)
                calculated_earnings[current_date] = calculated_book_values[current_date] * return_on_equity

            logging.info(
                "  Dividend Payout        : ${:.2f} (on {})".format(df.loc[last_time, ValueType.DIVIDEND_PAYOUT],
                                                                    last_time.strftime("%Y-%m-%d")))
            logging.info("  Dividends per Share    : ${:.2f}".format(dividends_per_share))
            logging.info("  Payout Ratio           : {:.2f}%".format(payout_ratio * 100.0))
            logging.info("  Retention Ratio        : {:.2f}%".format(retention_ratio * 100.0))
            logging.info("  Book Yield per Share   : {:.2f}%".format(book_yield_per_share * 100.0))
            logging.info("  Growth in Book Value   : {:.2f}%".format(book_value_growth * 100.0))
            logging.info("  Return on Equity (ROE) : {:.2f}%".format(return_on_equity * 100.0))

            logging.info("  - Estimate of Book Value per Share (using shares outstanding: {})".format(outstanding))
            logging.info("  Current    : ${:.2f} (on {})".format(book_value_per_share, last_time.strftime("%Y-%m-%d")))
            final_date = max(list(calculated_book_values.keys()))
            logging.info("  Calculated : ${:.2f} (on {})".format(calculated_book_values[final_date],
                                                                 final_date.strftime("%Y-%m-%d")))

            logging.info("  - Estimate of Earnings per Share")
            logging.info("  Current    : ${:.2f} (on {})".format(earnings_per_share, last_time.strftime("%Y-%m-%d")))
            final_date = max(list(calculated_earnings.keys()))
            logging.info("  Calculated : ${:.2f} (on {})".format(calculated_earnings[final_date],
                                                                 final_date.strftime("%Y-%m-%d")))

            logging.info("  - Future P/E (using historic P/E ratios)")
            max_pe = max(pe_ratios)
            avg_pe = sum(pe_ratios) / len(pe_ratios)
            median_pe = median(pe_ratios)
            min_pe = min(pe_ratios)
            logging.info("  Max P/E: {:.2f}  Average P/E: {:.2f}  Median P/E: {:.2f}  Min P/E: {:.2f}  ".format(
                max_pe, avg_pe, median_pe, min_pe))

            # the predictions are from a linear regression and could be used, but instead we do as Buffet does:
            calculated_eps = calculated_earnings[final_date]  # predictions[ValueType.REPORTED_EPS]
            logging.info("  - Future Share Price (future P/E * future EPS ${})".format(round(calculated_eps, 2)))
            max_price = max_pe * calculated_eps
            avg_price = avg_pe * calculated_eps
            median_price = median_pe * calculated_eps
            min_price = min_pe * calculated_eps
            logging.info("  Max Price: ${:.2f}  Average Price: ${:.2f}  Median Price: ${:.2f}  Min Price: ${:.2f}".
                         format(max_price, avg_price, median_price, min_price))

            logging.info("  - Future Return on Investment (ROI)")
            common_dividends = {}
            roi_report = "  Common Dividends - "
            todays_price = df.loc[last_time, ValueType.CLOSE]
            cash_flows = [todays_price * -1]
            for date, earnings in calculated_earnings.items():
                common_dividends[date] = earnings * payout_ratio
                roi_report += "{}: {}  ".format(date.strftime("%Y-%m-%d"), round(common_dividends[date], 2))
                cash_flows += [common_dividends[date]]
            logging.info(roi_report)
            max_irr = round(numpy.irr(cash_flows + [max_price]) * 100, 4)
            irr_report = "Max: {}%".format(max_irr)
            avg_irr = round(numpy.irr(cash_flows + [avg_price]) * 100, 4)
            irr_report += "  Average: {}%".format(avg_irr)
            median_irr = round(numpy.irr(cash_flows + [median_price]) * 100, 4)
            irr_report += "  Median: {}%".format(median_irr)
            min_irr = round(numpy.irr(cash_flows + [min_price]) * 100, 4)
            min_irr = 0.0 if math.isnan(min_irr) else min_irr
            irr_report += "  Min: {}%".format(min_irr)
            logging.info("  Today's prices: ${} ({})".format(todays_price, last_time.strftime("%Y-%m-%d")))
            logging.info(
                "  Annual Expected Rate of Return (IRR) - {} on {}".format(irr_report, final_date.strftime("%Y-%m-%d")))

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
        y = column.values
        days_from_start = (column.index - start_time).days.to_numpy()
        x = days_from_start.reshape(-1, 1)
        model = linear_model.LinearRegression().fit(x, y)
        future_days = (future_time - start_time).days
        predictions = model.predict([[future_days]])
        # logging.info(df)
        return predictions[0]

    def plot_collections(self, collections, interval):
        script_dir = os.path.dirname(os.path.realpath(__file__))
        visual_date_dir = FileSystem.get_and_clean_cache_dir(
            os.path.join(script_dir, '..', '..', '..', '.cache', 'visuals'))
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
