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
import os.path
import time
from datetime import datetime, timedelta
from enum import Enum
from os import environ
from typing import Optional, List

import pandas

from main.application.adapter import AssetType, Adapter, insert_column
from main.application.time_interval import TimeInterval
from main.application.value_type import ValueType
from main.application.converter import Converter
from main.application.argument import ArgumentKey


class NoDataReturnedException(RuntimeError):
    pass


class OrderedOutput(Enum):
    RSI = 0
    MACD = 0
    MACD_SIGNAL = 1
    MACD_HIST = 2


class IexCloud(Adapter):
    name: str = 'iexCloud'
    url: str = 'https://cloud.iexapis.com/stable'

    def __init__(self, symbol: str, asset_type: Optional[AssetType]):
        if environ.get('IEX_CLOUD_API_KEY') is None:
            raise RuntimeError(
                "The IEX_CLOUD_API_KEY environment variable is not set - this needs to be set to the API KEY for "
                "your account from the alphavantage.co site.")
        self.api_key = environ.get('IEX_CLOUD_API_KEY')
        super().__init__(symbol)
        # script_dir = os.path.dirname(os.path.realpath(__file__))
        # cache_dir = os.path.join(script_dir, '..', '..', '..', '..', '.cache', IexCloud.name)
        # self.cache_root_dir = os.path.realpath(cache_dir)
        self.converters: List[Converter] = [
            # we allow for multiple strings to be converted into the value type, first match is used
            Converter(ValueType.OPEN, self.get_prices_response, ['open'], adjust_values=True),
            Converter(ValueType.HIGH, self.get_prices_response, ['high'], adjust_values=True),
            Converter(ValueType.LOW, self.get_prices_response, ['low'], adjust_values=True),
            Converter(ValueType.CLOSE, self.get_prices_response, ['close'], adjust_values=True),
            Converter(ValueType.VOLUME, self.get_prices_response, ['volume']),
            Converter(ValueType.RSI, self.get_rsi_response, [OrderedOutput.RSI.value]),
            Converter(ValueType.MACD, self.get_macd_response, [OrderedOutput.MACD.value]),
            Converter(ValueType.MACD_HIST, self.get_macd_response, [OrderedOutput.MACD_HIST.value]),
            Converter(ValueType.MACD_SIGNAL, self.get_macd_response, [OrderedOutput.MACD_SIGNAL.value]),
            # SMA = auto()
            # BOOK = auto()
            Converter(ValueType.EPS, self.get_reported_financials_response,
                      ['EarningsPerShareDiluted', 'EarningsPerShareBasicAndDiluted']),
            # Converter(ValueType.REPORTED_EPS, self.get_earnings_response, ['reportedEPS']),
            # ESTIMATED_EPS = auto()
            # SURPRISE_EPS = auto()
            # SURPRISE_PERCENTAGE_EPS = auto()
            # GROSS_PROFIT = auto()
            # TOTAL_REVENUE = auto()
            # OPERATING_CASH_FLOW = auto()
            Converter(ValueType.DIVIDENDS, self.get_cash_flow_response, ['dividendsPaid']),
            Converter(ValueType.NET_INCOME, self.get_income_response, ['netIncomeBasic']),

            Converter(ValueType.ASSETS, self.get_balance_sheet_response, ['Assets', 'totalAssets']),
            Converter(ValueType.LIABILITIES, self.get_balance_sheet_response,
                      ['Liabilities', 'totalLiabilities']),

            # This value was very wrong for BRK-A, it says something like 3687360528 shares outstanding, while there
            # are actually only something like 640000
            Converter(ValueType.SHARES, self.get_reported_financials_response,
                      ['WeightedAverageNumberOfSharesOutstandingBasic', 'CommonStockSharesOutstanding', 'commonStock']),
            # This is not quite right...
            # https://www.fool.com/investing/stock-market/basics/earnings-per-share/

            # Let's walk through an example EPS calculation using Netflix (NASDAQ:NFLX). For its most recent fiscal
            # year, the company reported a net income of $2,761,395,000 and total shares outstanding of 440,922,
            # 000. The company's balance sheet indicates Netflix has not issued any preferred stock, so we don't need
            # to subtract out preferred dividends. Dividing $2,761,395,000 into 440,922,000 produces an EPS value of
            # $6.26. (this is what we get, and even then the number of outstanding shares differs slightly)
            #
            # Let's calculate the diluted EPS for Netflix. The company has granted 13,286,000 stock options to
            # employees, which raises the total outstanding share count to 454,208,000. Dividing the same $2,761,395,
            # 000 of net income into 454,208,000 equals an EPS value of $6.08.
            Converter(ValueType.DILUTED_SHARES, self.get_reported_financials_response,
                      ['WeightedAverageNumberOfDilutedSharesOutstanding', 'CommonStockSharesOutstanding',
                       'commonStock']),
            Converter(ValueType.EQUITY, self.get_reported_financials_response,
                      ['StockholdersEquity', 'shareholderEquity']),
        ]

    @staticmethod
    def find_symbol_in_data(data, entry):
        contains = False
        for row in data:
            if row[0] == entry:
                contains = True
                break
        return contains

    def get_equities_list(self):
        query = {
            "token": self.api_key,
        }
        data, data_file = self.get_url_response('{}/ref-data/symbols'.format(self.url), query)
        data = [item['symbol'] for item in data]
        return data

    def get_span(self, default: timedelta = timedelta(weeks=52)) -> timedelta:
        start_time: datetime = self.get_argument_value(ArgumentKey.START_TIME)
        start_time = start_time if start_time is not None else datetime.now()
        end_time: datetime = self.get_argument_value(ArgumentKey.END_TIME)
        end_time = end_time if end_time is not None else start_time + default
        delta: timedelta = end_time - start_time
        return delta

    def get_span_as_str(self) -> str:
        delta: timedelta = self.get_span()
        if delta <= TimeInterval.DAY.timedelta:
            # if self.series_interval == TimeInterval.DAY:
            series_range = '1d'
        elif delta <= TimeInterval.WEEK.timedelta:
            # elif self.series_interval == TimeInterval.WEEK:
            series_range = '1w'
        elif delta <= TimeInterval.MONTH.timedelta:
            series_range = '1m'
        elif delta <= TimeInterval.QUARTER.timedelta:
            series_range = '3m'
        elif delta <= TimeInterval.YEAR.timedelta:
            series_range = '1y'
        elif delta <= TimeInterval.YEAR2.timedelta:
            series_range = '2y'
        elif delta <= TimeInterval.YEAR5.timedelta:
            series_range = '5y'
        else:
            series_range = 'max'
        return series_range

    def get_prices_response(self, value_type: ValueType):
        query = {"token": self.api_key, }
        series_range = self.get_span_as_str()
        raw_response, data_file = self.get_url_response('{}/stock/{}/chart/{}'.format(
            self.url,
            self.symbol,
            series_range),
            query)
        self.translate(raw_response, value_type)

    # def translate(self, response_data, data_date_format='%Y-%m-%d'):
    #     if not response_data:
    #         raise RuntimeError("There is no data (length is 0) for (maybe try a different time interval)")
    #     translated = {}
    #     for entry in response_data:
    #         dt = datetime.strptime(entry['date'], data_date_format)
    #         translated[dt] = {}
    #         for series_type in ValueType:
    #             value = self.get_response_value_or_none(entry, series_type)
    #             if value is not None:
    #                 ratio = self.get_adjusted_ratio(entry)
    #                 value = value * ratio
    #                 translated[dt][series_type] = value
    #     return translated

    def translate(self, response_data, value_type: ValueType, data_date_format='%Y-%m-%d'):
        for converter in self.converters:
            if converter.value_type in self.data:
                continue  # if we've already added this value type, then don't do it again
            if converter.value_type != value_type:
                continue
            indexes = []
            values = []
            for entry in response_data:
                value = None
                for response_key, response_value in entry.items():
                    if response_key in converter.response_keys:
                        value = 0.0 if response_value == 'None' else float(response_value)
                        break
                if value is not None:
                    indexes.append(datetime.strptime(entry['date'], data_date_format))
                    values.append(value)
            insert_column(self.data, converter.value_type, indexes, values)
        assert value_type in self.data, "Parsing response data failed, was adding column for value type '{}', but " \
                                        "no data was present after getting and parsing the response. Does the " \
                                        "converter have the correct keys/locations for the raw data?".format(value_type)

    def get_digital_series_response(self):
        if self.series_interval == TimeInterval.DAY:
            function = "DIGITAL_CURRENCY_DAILY"
            key = 'Time Series (Digital Currency Daily)'
        elif self.series_interval == TimeInterval.WEEK:
            function = "DIGITAL_CURRENCY_WEEKLY"
            key = 'Time Series (Digital Currency Weekly)'
        elif self.series_interval == TimeInterval.MONTH:
            function = "DIGITAL_CURRENCY_MONTHLY"
            key = 'Time Series (Digital Currency Monthly)'
        else:
            raise RuntimeError(
                'Interval is not supported: {} (for: {})'.format(self.series_interval, self.__class__.__name__))
        query = {
            "token": self.api_key,
            "function": function,
            "symbol": self.symbol,
            "market": self.base_symbol,
        }
        raw_response, data_file = self.get_url_response(self.url, query)
        self.validate_json_response(data_file, raw_response)
        data = self.translate(raw_response, key)
        return data

    def get_macd_response(self, value_type: ValueType):
        series_range = self.get_span_as_str()
        slow: float = self.get_argument_value(ArgumentKey.MACD_SLOW)
        fast: float = self.get_argument_value(ArgumentKey.MACD_FAST)
        signal: float = self.get_argument_value(ArgumentKey.MACD_SIGNAL)
        query = {
            "token": self.api_key,
            "range": series_range,
            "fast": int(fast),
            "slow": int(slow),
            "signal": int(signal),
        }
        raw_response, data_file = self.get_url_response('{}/stock/{}/indicator/{}'.format(
            self.url,
            self.symbol,
            'macd',
        ),
            query)
        self.translate_map(raw_response, value_type)
        # indicator_key = self.get_indicator_key()  # e.g. BTCUSD
        # query = {
        #     "token": self.api_key,
        #     "function": "MACD",
        #     "symbol": indicator_key,
        #     "interval": self.macd_interval.value,
        #     "slowperiod": int(self.macd_slow_period),
        #     "fastperiod": int(self.macd_fast_period),
        #     "signalperiod": int(self.macd_signal_period),
        #     "series_type": self.macd_series_type.value,
        # }
        # raw_response, data_file = self.get_url_response(self.url, query)
        # self.validate_json_response(data_file, raw_response)
        # data = self.translate(raw_response, 'Technical Analysis: MACD')
        # return data

    def get_sma_response(self, value_type: ValueType):
        indicator_key = self.get_indicator_key()  # e.g. BTCUSD
        query = {
            "token": self.api_key,
            "function": "SMA",
            "symbol": indicator_key,
            "interval": self.sma_interval.value,
            "time_period": self.sma_period,
            "series_type": self.sma_series_type,
        }
        raw_response, data_file = self.get_url_response(self.url, query)
        self.validate_json_response(data_file, raw_response)
        key = 'Technical Analysis: SMA'
        data = self.translate(raw_response, value_type, key)
        return data

    def get_rsi_response(self, value_type: ValueType):
        series_range = self.get_span_as_str()
        period: float = self.get_argument_value(ArgumentKey.RSI_PERIOD)
        query = {
            "token": self.api_key,
            "range": series_range,
            "period": period,
        }
        raw_response, data_file = self.get_url_response('{}/stock/{}/indicator/{}'.format(
            self.url,
            self.symbol,
            'rsi',
        ),
            query)
        self.translate_map(raw_response, value_type)
        # indicator_key = self.get_indicator_key()  # e.g. BTCUSD
        # query = {
        #     "token": self.api_key,
        #     "function": "RSI",
        #     "symbol": indicator_key,
        #     "interval": self.rsi_interval.value,
        #     "time_period": int(self.rsi_period),
        #     "series_type": self.rsi_series_type.value,
        # }
        # raw_response, data_file = self.get_url_response(self.url, query)
        # self.validate_json_response(data_file, raw_response)
        # key = 'Technical Analysis: RSI'
        # data = self.translate(raw_response, key)
        # return data

    def translate_map(self, response_data, value_type: ValueType, data_date_format='%Y-%m-%d'):
        indicator_keys = ['indicator', 'Indicator']
        chart_key = 'chart'
        if chart_key not in response_data:
            raise RuntimeError("Failed to find key in data: {}".format(chart_key))
        if not response_data[chart_key]:
            raise RuntimeError(
                "There is no data (length is 0) for key: {} (maybe try a different time interval)".format(chart_key))
        for converter in self.converters:
            if converter.value_type in self.data:
                continue  # if we've already added this value type, then don't do it again
            if converter.value_type != value_type:
                continue
            indexes = []
            values = []
            for idx, entry in enumerate(response_data[chart_key]):
                value = None
                for response_key in converter.response_keys:
                    indicator_key = [k for k in indicator_keys if k in response_data][0]
                    value = response_data[indicator_key][response_key][idx]
                    # value = 0.0 if response_value == 'None' else float(response_value)
                    break
                if value is not None:
                    indexes.append(datetime.strptime(entry['date'], data_date_format))
                    values.append(value)
            insert_column(adapter.data, converter.value_type, indexes, values)
        assert value_type in self.data, "Parsing response data failed, was adding column for value type '{}', but " \
                                        "no data was present after getting and parsing the response. Does the " \
                                        "converter have the correct keys/locations for the raw data?".format(value_type)


    def get_earnings_response(self):
        interval: TimeInterval = self.get_argument_value(ArgumentKey.INTERVAL)
        if interval.timedelta <= TimeInterval.QUARTER.timedelta:
            period = 'quarter'
        elif interval.timedelta <= TimeInterval.YEAR.timedelta:
            period = 'annual'
        else:
            raise RuntimeError(
                'Interval is not supported: {} (for: {})'.format(interval, self.__class__.__name__))
        last = self.get_span() / interval.timedelta
        query = {
            'token': self.api_key,
            'period': period,
            'last': last,
        }
        query = {'token': self.api_key, 'period': period, 'last': last}
        raw_response, data_file = self.get_url_response('{}/stock/{}/earnings'.format(
            self.url,
            self.symbol),
            query)
        key = 'earnings'
        self.translate_earnings(raw_response, key)

    def translate_earnings(self, response_data, key, data_date_format='%Y-%m-%d'):
        if key not in response_data:
            raise RuntimeError("Failed to find key in data: {}".format(key))
        if not response_data[key]:
            raise RuntimeError(
                "There is no data (length is 0) for key: {} (maybe try a different time interval)".format(key))
        for converter in self.converters:
            if converter.value_type in self.data:
                continue  # if we've already added this value type, then don't do it again
            indexes = []
            values = []
            for entry in response_data[key]:
                value = None
                for response_key, response_value in entry.items():
                    if response_key in converter.response_keys:
                        value = 0.0 if response_value == 'None' else float(response_value)
                        break
                if value is not None:
                    indexes.append(datetime.strptime(entry['fiscalDateEnding'], data_date_format))
                    values.append(value)
            insert_column(adapter.data, converter.value_type, indexes, values)

    def get_income_response(self, value_type: ValueType):
        interval: TimeInterval = self.get_argument_value(ArgumentKey.INTERVAL)
        if interval.timedelta <= TimeInterval.QUARTER.timedelta:
            period = 'quarter'
        elif interval.timedelta <= TimeInterval.YEAR.timedelta:
            period = 'annual'
        else:
            raise RuntimeError(
                'Interval is not supported: {} (for: {})'.format(interval, self.__class__.__name__))
        last = self.get_span() / interval.timedelta
        query = {'token': self.api_key, 'period': period, 'last': last}
        raw_response, data_file = self.get_url_response('{}/stock/{}/income'.format(
            self.url,
            self.symbol),
            query)
        self.validate_json_data(raw_response, data_file)
        key = 'income'
        self.translate_income(raw_response, value_type, key)

    def translate_income(self, response_data, value_type: ValueType, key, data_date_format='%Y-%m-%d'):
        if key not in response_data:
            raise RuntimeError("Failed to find key in data: {}".format(key))
        if not response_data[key]:
            raise RuntimeError(
                "There is no data (length is 0) for key: {} (maybe try a different time interval)".format(key))
        converter = self.get_converter(value_type)
        if converter.value_type in self.data:
            return  # if we've already added this value type, then don't do it again
        indexes = []
        values = []
        for entry in response_data[key]:
            value = None
            for response_key in converter.response_keys:
                if response_key not in entry:
                    continue
                response_value = entry[response_key]
                value = 0.0 if response_value == 'None' else float(response_value)
                break
            if value is not None:
                indexes.append(datetime.strptime(entry['fiscalDate'], data_date_format))
                values.append(value)
        insert_column(adapter.data, converter.value_type, indexes, values)

    # def translate_income(self, response_data, key, data_date_format='%Y-%m-%d'):
    #     if key not in response_data:
    #         raise RuntimeError("Failed to find key in data: {}".format(key))
    #     if not response_data[key]:
    #         raise RuntimeError(
    #             "There is no data (length is 0) for key: {} (maybe try a different time interval)".format(key))
    #     translated = {}
    #     for entry in response_data[key]:
    #         dt = datetime.strptime(entry['fiscalDate'], data_date_format)
    #         translated[dt] = {}
    #         for series_type in ValueType:
    #             value = self.get_response_value_or_none(entry, series_type)
    #             if value is not None:
    #                 ratio = self.get_adjusted_ratio(entry)
    #                 value = value * ratio
    #                 translated[dt][series_type] = value
    #     return translated
    #
    def get_balance_sheet_response(self, value_type: ValueType):
        interval: TimeInterval = self.get_argument_value(ArgumentKey.INTERVAL)
        if interval.timedelta <= TimeInterval.QUARTER.timedelta:
            period = 'quarter'
        elif interval.timedelta <= TimeInterval.YEAR.timedelta:
            period = 'annual'
        else:
            raise RuntimeError('Interval is not supported: {} (for: {})'.format(interval, self.__class__.__name__))
        last = int(self.get_span() / interval.timedelta)
        query = {'token': self.api_key, 'period': period, 'last': last}
        raw_response, data_file = self.get_url_response('{}/stock/{}/balance-sheet'.format(self.url, self.symbol),
                                                        query)
        self.validate_json_data(raw_response, data_file)
        key = 'balancesheet'
        self.translate_balance_sheet(raw_response, value_type, key)

    def translate_balance_sheet(self, response_data, value_type: ValueType, key, data_date_format='%Y-%m-%d'):
        if key not in response_data:
            raise RuntimeError("Failed to find key in data: {}".format(key))
        if not response_data[key]:
            raise RuntimeError(
                "There is no data (length is 0) for key: {} (maybe try a different time interval)".format(key))
        for converter in self.converters:
            if converter.value_type in self.data:
                continue  # if we've already added this value type, then don't do it again
            indexes = []
            values = []
            for entry in response_data[key]:
                value = None
                for response_key, response_value in entry.items():
                    if response_key in converter.response_keys:
                        value = 0.0 if response_value == 'None' or response_value is None else float(response_value)
                        break
                if value is not None:
                    indexes.append(datetime.strptime(entry['fiscalDate'], data_date_format))
                    values.append(value)
            insert_column(adapter.data, converter.value_type, indexes, values)

    def get_reported_financials_response(self, value_type: ValueType):
        interval: TimeInterval = self.get_argument_value(ArgumentKey.INTERVAL)
        if interval.timedelta <= TimeInterval.QUARTER.timedelta:
            period = '10-Q'
        elif interval.timedelta <= TimeInterval.YEAR.timedelta:
            period = '10-K'
        else:
            raise RuntimeError('Interval is not supported: {} (for: {})'.format(interval, self.__class__.__name__))
        end_time: datetime = self.get_argument_value(ArgumentKey.END_TIME)
        end_time = end_time if end_time is not None else datetime.now()
        default: timedelta = timedelta(weeks=52)
        start_time: datetime = self.get_argument_value(ArgumentKey.START_TIME)
        start_time = start_time if start_time is not None else end_time - default
        date_format = '%Y-%m-%d'
        query = {'token': self.api_key, 'from': start_time.strftime(date_format)}
        # query = {'token': self.api_key, 'from': start_time.strftime(date_format), 'to': end_time.strftime(date_format)}
        # last = int(self.get_span() / interval.timedelta)
        # query = {'token': self.api_key, 'last': last}
        raw_response, data_file = self.get_url_response(
            '{}/time-series/reported_financials/{}/{}'.format(self.url, self.symbol, period), query)
        # self.translate_fundamentals(raw_response)
        self.validate_json_data(raw_response, data_file)
        self.translate_financials(raw_response, value_type)

    def validate_json_data(self, data, data_file):
        if not data:
            raise NoDataReturnedException(f"No data was returned for {self} (file: {data_file}), data: {data}")

    def translate_financials(self, response_data, value_type: ValueType, data_date_format='%Y-%m-%d'):
        indexes: List[datetime] = []  # NOTE: in case one value type is missing from some entries
        updates: List[datetime] = []  # we store the indexes for each value type
        values: List[float] = []
        converter = self.get_converter(value_type)
        if converter.value_type in self.data:
            return  # if we've already added this value type, then don't do it again
        for entry in response_data:
            instance = datetime.fromtimestamp(entry['periodEnd'] / 1000)
            # instance = datetime.strptime(entry['formFiscalYear'], '%Y')
            updated = datetime.fromtimestamp(entry['updated'] / 1000)
            for response_key in converter.response_keys:
                if response_key not in entry:
                    continue
                response_value = entry[response_key]
                value = 0.0 if response_value == 'None' else float(response_value)
                assert type(value) is float, f"After parsing response value '{response_value}' for key " \
                                             f"'{response_key}', the type was expected to be a 'float' but was " \
                                             f"instead: '{type(value)}'"
                if instance in indexes:
                    # same time, then need to check the 'updated' time and use the latest
                    location = indexes.index(instance)
                    if updated > updates[location]:
                        logging.debug(f"Updating entry for period ending {instance}, as a more recent update "
                                      f"{updated} was found (current record was updated "
                                      f"{updates[location]}, entry {converter.value_type}).")
                        # indexes[location] = instance  # these are already the same
                        updates[location] = updated
                        values[location] = value
                        continue
                    else:
                        logging.debug(f"Skipping entry for period ending {instance}, as this record was updated "
                                      f"{updated} and we already have a record that is more recent (current record "
                                      f"was updated {updates[location]}, entry {converter.value_type}).")
                        continue
                indexes.append(instance)  # these are already the same
                updates.append(updated)
                values.append(value)
        insert_column(adapter.data, converter.value_type, indexes, values)
        # max_entries = 0
        # if converter.value_type in indexes:
        #     max_entries = max(max_entries, len(indexes))
        #     self.insert_data_column(converter.value_type, indexes,
        #                             values)
        # if converter.value_type in indexes:
        #     if len(indexes) < max_entries:
        #         logging.warning(f"The '{converter.value_type}' value type appears to have missing entries, "
        #                         f"only has entries for {[str(d) for d in indexes]}. Perhaps "
        #                         f"a new response key should be added, the currently searched for response keys "
        #                         f"are: {converter.response_keys}")
        assert value_type in self.data, "Parsing response data failed, was adding column for value type '{}', but " \
                                        "no data was present after getting and parsing the response. Does the " \
                                        "converter have the correct keys/locations for the raw data?".format(value_type)

    def translate_fundamentals(self, response_data, data_date_format='%Y-%m-%d'):
        for converter in self.converters:
            if converter.value_type in self.data:
                continue  # if we've already added this value type, then don't do it again
            indexes = []
            values = []
            for entry in response_data:
                for series_type in ValueType:
                    value = get_response_value_or_none(entry, series_type)
                    if value is not None:
                        indexes.append(datetime.fromtimestamp(entry['periodEnd'] / 1000))
                        # indexes.append(datetime.strptime(entry['periodEnd'], data_date_format))
                        ratio = self.get_adjusted_ratio(entry)
                        value = value * ratio
                        values.append(value)
            insert_column(adapter.data, converter.value_type, indexes, values)

    def calculate_eps(self):
        # Represents net income available to common basic EPS before extraordinaries for the period calculated as (
        # net income after preferred dividends) - (discontinued operations)
        self.retrieve(ValueType.NET_INCOME)
        net_income_basic: pandas.Series = self.data.loc[:, ValueType.NET_INCOME]
        self.retrieve(ValueType.DILUTED_SHARES)
        diluted_shares: pandas.Series = self.data.loc[:, ValueType.DILUTED_SHARES]
        self.data.loc[:, ValueType.EPS] = net_income_basic / diluted_shares

    def get_cash_flow_response(self, value_type: ValueType):
        interval: TimeInterval = self.get_argument_value(ArgumentKey.INTERVAL)
        if interval.timedelta <= TimeInterval.QUARTER.timedelta:
            period = 'quarter'
        elif interval.timedelta <= TimeInterval.YEAR.timedelta:
            period = 'annual'
        else:
            raise RuntimeError(
                'Interval is not supported: {} (for: {})'.format(interval, self.__class__.__name__))
        last = self.get_span() / interval.timedelta
        query = {'token': self.api_key, 'period': period, 'last': last}
        raw_response, data_file = self.get_url_response('{}/stock/{}/cash-flow'.format(
            self.url,
            self.symbol),
            query)
        key = 'cashflow'
        self.validate_json_data(raw_response, data_file)
        self.translate_balance_sheet(raw_response, value_type, key)
        # self.translate_cash_flow(raw_response, key)

    # def translate_cash_flow(self, response_data, key, data_date_format='%Y-%m-%d'):
    #     if key not in response_data:
    #         raise RuntimeError("Failed to find key in data: {}".format(key))
    #     if not response_data[key]:
    #         raise RuntimeError(
    #             "There is no data (length is 0) for key: {} (maybe try a different time interval)".format(key))
    #     translated = {}
    #     for entry in response_data[key]:
    #         dt = datetime.strptime(entry['fiscalDate'], data_date_format)
    #         translated[dt] = {}
    #         for series_type in ValueType:
    #             value = self.get_response_value_or_none(entry, series_type)
    #             if value is not None:
    #                 ratio = self.get_adjusted_ratio(entry)
    #                 value = value * ratio
    #                 translated[dt][series_type] = value
    #     return translated

    @staticmethod
    def validate_json_response(data_file, raw_response):
        if "Error Message" in raw_response:
            raise RuntimeError(
                "Error message in response - {}\n  See: {}".format(raw_response["Error Message"], data_file))
        if "Note" in raw_response:
            raise RuntimeError("Note message in response - {}\n  See: {}".format(raw_response["Note"], data_file))
        if not "Meta Data" in raw_response:
            raise RuntimeError(
                "Failed to find the meta data in response: {} (perhaps the currency doesn't support "
                "this)".format(
                    data_file))

    def get_indicator_key(self):
        self.calculate_asset_type()
        indicator_key = self.symbol
        if self.asset_type == AssetType.DIGITAL_CURRENCY:
            indicator_key = self.symbol + self.base_symbol  # e.g. BTCUSD
        return indicator_key

    def delay_requests(self, data_file):
        wait = True
        while wait:
            # NOTE: there is a race condition here if running multi-process...
            #       files could be created between when you read their create times and return thus allowing more than
            #       X (i.e. 5 for this adapter) requests per allotted timeframe (i.e. minute for this)
            #       to fix this you could create yet another lock here, but for now we limit to 1 request at a time
            #       and that elegantly fixes this as well as prevents us from hammering servers ;)
            historic_requests: dict = self.get_create_times()
            wait_list = []
            now: datetime = datetime.now()
            closest = now + timedelta(minutes=1)
            for key, request_time in historic_requests.items():
                reset_time = request_time + timedelta(minutes=1)
                if reset_time > now:
                    wait_list.append(key)
                    if reset_time < closest:
                        closest = reset_time
            if len(wait_list) >= 5:
                sleep = closest - now
                buffer = 10 / 1000.0
                sleep_in_s = buffer + sleep.seconds + sleep.microseconds / 1000000.0
                logging.info('-- Waiting for: {} = closest:{} - now:{}'.format(sleep_in_s, closest, now))
                # logging.info('MAP: {}'.format(json.dumps(self.historicRequests, indent=2, default=str)))
                time.sleep(sleep_in_s)
            else:
                wait = False

    def get_create_times(self):
        cache_requests = {}
        date_dir = os.path.join(self.cache_root_dir, self.cache_key_date.strftime('%Y%m%d'))
        for filename in os.listdir(date_dir):
            file_path = os.path.join(date_dir, filename)
            if filename.startswith(".lock"):
                continue
            cache_requests[file_path] = datetime.fromtimestamp(os.stat(file_path).st_ctime)
            # modTimesinceEpoc = os.path.getmtime(file_path)
        return cache_requests

    def get_is_digital_currency(self):
        query = {"token": self.api_key}
        data, data_file = self.get_url_response('{}/ref-data/crypto/symbols'.format(self.url), query)
        data = [item['symbol'] for item in data]
        return '{}{}'.format(self.symbol, self.base_symbol) in data

    def get_is_listed(self) -> bool:
        data = self.get_equities_list()
        return self.symbol in data

    def get_is_physical_currency(self):
        query = {"token": self.api_key}
        data, data_file = self.get_url_response('{}/ref-data/fx/symbols'.format(self.url), query)
        data = [item['code'] for item in data['currencies']]
        return self.base_symbol in data
