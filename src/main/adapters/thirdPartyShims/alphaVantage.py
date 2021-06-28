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
from os import environ
from typing import Dict, List, Optional

from main.adapters.adapter import DataType, TimeInterval, AssetType, Adapter
from main.adapters.valueType import ValueType
from main.adapters.converter import Converter
from main.adapters.argument import ArgumentType


class AlphaVantage(Adapter):
    name: str = 'alphaVantage'
    url: str = 'https://www.alphavantage.co/query'

    def __init__(self, symbol: str, asset_type: Optional[AssetType]):
        if environ.get('ALPHA_VANTAGE_API_KEY') is None:
            raise RuntimeError(
                "The ALPHA_VANTAGE_API_KEY environment variable is not set - this needs to be set to the API KEY for "
                "your account from the alphavantage.co site.")
        api_key = environ.get('ALPHA_VANTAGE_API_KEY')
        super().__init__(symbol, asset_type)
        self.api_key = api_key
        script_dir = os.path.dirname(os.path.realpath(__file__))
        cache_dir = os.path.join(script_dir, '..', '..', '..', '..', '.cache', AlphaVantage.name)
        self.cache_dir = os.path.realpath(cache_dir)
        self.converters: List[Converter] = [
            # we allow for multiple strings to be converted into the value type, first match is used
            Converter(ValueType.OPEN, self.get_prices_response, ['1. open', '1a. open (USD)'], adjust_values=True),
            Converter(ValueType.HIGH, self.get_prices_response, ['2. high', '2a. high (USD)'], adjust_values=True),
            Converter(ValueType.LOW, self.get_prices_response, ['3. low', '3a. low (USD)'], adjust_values=True),
            Converter(ValueType.CLOSE, self.get_prices_response, ['4. close', '4a. close (USD)'], adjust_values=True),
            Converter(ValueType.VOLUME, self.get_prices_response, ['5. volume']),
            Converter(ValueType.RSI, self.get_rsi_response, ['RSI']),
            Converter(ValueType.MACD, self.get_macd_response, ['MACD']),
            Converter(ValueType.MACD_HIST, self.get_macd_response, ['MACD_Hist']),
            Converter(ValueType.MACD_SIGNAL, self.get_macd_response, ['MACD_Signal']),
            # SMA = auto()
            # BOOK = auto()
            Converter(ValueType.REPORTED_EPS, self.get_earnings_response, ['reportedEPS']),
            # ESTIMATED_EPS = auto()
            # SURPRISE_EPS = auto()
            # SURPRISE_PERCENTAGE_EPS = auto()
            # GROSS_PROFIT = auto()
            # TOTAL_REVENUE = auto()
            # OPERATING_CASH_FLOW = auto()
            Converter(ValueType.DIVIDEND_PAYOUT, self.get_cash_flow_response, ['dividendPayout']),
            Converter(ValueType.NET_INCOME, self.get_cash_flow_response, ['netIncome']),
            Converter(ValueType.TOTAL_ASSETS, self.get_balance_sheet_response, ['totalAssets']),
            Converter(ValueType.TOTAL_LIABILITIES, self.get_balance_sheet_response, ['totalLiabilities']),
            # This value was very wrong for BRK-A, it says something like 3687360528 shares outstanding, while there
            # are actually only something like 640000
            Converter(ValueType.OUTSTANDING_SHARES, self.get_balance_sheet_response, ['commonStockSharesOutstanding']),
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
            Converter(ValueType.DILUTED_SHARES, self.get_balance_sheet_response, ['commonStockSharesOutstanding']),
            Converter(ValueType.TOTAL_SHAREHOLDER_EQUITY, self.get_balance_sheet_response, ['totalShareholderEquity']),
        ]

    def get_adjusted_ratio(self, time_data: Dict[str, str]) -> float:
        adjusted_close = self.get_response_value_or_none(time_data, '5. adjusted close')
        # adjusted_close = self.get_value_or_none(time_data, ValueType.ADJUSTED_CLOSE)
        close = self.get_response_value_or_none(time_data, '4. close')
        ratio = 1.0 if (adjusted_close is None) or (close is None) else adjusted_close / close
        return float(ratio)

    def find_symbol_in_data(self, data, entry):
        contains = False
        for row in data:
            if row[0] == entry:
                contains = True
                break
        return contains

    def get_equities_list(self):
        query = {
            "apikey": self.api_key,
            "function": "LISTING_STATUS",
        }
        data, data_file = self.get_url_response(self.url, query, cache=True, data_type=DataType.CSV)
        data = data[1:]  # remove header
        data = [item[0] for item in data]
        return data

    def get_prices_response(self) -> None:
        if self.asset_type is AssetType.DIGITAL_CURRENCY:
            self.get_digital_currency_response()
        else:
            self.get_stock_prices_response()

    def get_stock_prices_response(self) -> None:
        query = {}
        query["apikey"] = self.api_key
        query["symbol"] = self.symbol
        # data_date_format = '%Y-%m-%d'
        interval: TimeInterval = self.get_argument_value(ArgumentType.INTERVAL)
        if interval == TimeInterval.HOUR:
            query["function"] = "TIME_SERIES_INTRADAY"
            query["interval"] = TimeInterval.HOUR.value
            query["adjusted"] = True
            query["outputsize"] = "full"
            key = 'Time Series (60min)'
            # data_date_format = '%Y-%m-%d %H:%M:%S'
        elif interval == TimeInterval.DAY:
            query["function"] = "TIME_SERIES_DAILY_ADJUSTED"
            query["outputsize"] = "full"
            key = 'Time Series (Daily)'
        elif interval == TimeInterval.WEEK:
            query["function"] = "TIME_SERIES_WEEKLY_ADJUSTED"
            key = 'Weekly Adjusted Time Series'
        elif interval == TimeInterval.MONTH:
            query["function"] = "TIME_SERIES_MONTHLY_ADJUSTED"
            key = 'Monthly Adjusted Time Series'
        else:
            raise RuntimeError(
                'Specified interval is not supported: \'{}\' (for: {})'.format(interval, self.__class__.__name__))
        raw_response, data_file = self.get_url_response(self.url, query)
        self.validate_json_response(data_file, raw_response)
        self.translate(raw_response, key)

    def get_digital_currency_response(self) -> None:
        query = {}
        query["apikey"] = self.api_key
        query["symbol"] = self.symbol
        query["market"] = self.base_symbol
        interval: TimeInterval = self.get_argument_value(ArgumentType.INTERVAL)
        if interval == TimeInterval.DAY:
            query["function"] = "DIGITAL_CURRENCY_DAILY"
            key = 'Time Series (Digital Currency Daily)'
        elif interval == TimeInterval.WEEK:
            query["function"] = "DIGITAL_CURRENCY_WEEKLY"
            key = 'Time Series (Digital Currency Weekly)'
        elif interval == TimeInterval.MONTH:
            query["function"] = "DIGITAL_CURRENCY_MONTHLY"
            key = 'Time Series (Digital Currency Monthly)'
        else:
            raise RuntimeError(
                'Interval is not supported: {} (for: {})'.format(interval, self.__class__.__name__))
        raw_response, data_file = self.get_url_response(self.url, query)
        self.validate_json_response(data_file, raw_response)
        self.translate(raw_response, key)

    def translate(self, response_data, key, data_date_format='%Y-%m-%d') -> None:
        """

        :param response_data: Data from an API or URL request (raw data generally JSON, CSV, etc.)
        :param key: The root key where we will pull the dictionary out of
        :param data_date_format: The incoming data time format, used to convert to datetime objects
        :return: None
        """
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
            for entry_datetime, response_entry in response_data[key].items():
                value = None
                for response_key, response_value in response_entry.items():
                    if response_key in converter.response_keys:
                        value = float(response_value)
                        break
                if value is None:  # we didn't find a match so move on to the next thing to convert
                    continue
                if converter.adjust_values:
                    ratio = self.get_adjusted_ratio(response_entry)
                    value = value * ratio
                indexes.append(datetime.strptime(entry_datetime, data_date_format))
                values.append(value)
            self.insert_data_column(converter.value_type, indexes, values)

    def get_macd_response(self) -> None:
        indicator_key = self.get_indicator_key()  # e.g. BTCUSD
        query = {
            "apikey": self.api_key,
            "symbol": indicator_key,
            "function": "MACD",
            "interval": self.get_argument_value(ArgumentType.INTERVAL).value,
            "slowperiod": int(self.get_argument_value(ArgumentType.MACD_SLOW)),
            "fastperiod": int(self.get_argument_value(ArgumentType.MACD_FAST)),
            "signalperiod": int(self.get_argument_value(ArgumentType.MACD_SIGNAL)),
            "series_type": "close"
        }
        raw_response, data_file = self.get_url_response(self.url, query)
        self.validate_json_response(data_file, raw_response)
        self.translate(raw_response, 'Technical Analysis: MACD')

    def get_sma_response(self):
        indicator_key = self.get_indicator_key()  # e.g. BTCUSD
        query = {
            "apikey": self.api_key,
            "symbol": indicator_key,
            "function": "SMA",
            "interval": self.sma_interval.value,
            "time_period": self.sma_period,
            "series_type": self.sma_series_type,
        }
        raw_response, data_file = self.get_url_response(self.url, query)
        self.validate_json_response(data_file, raw_response)
        key = 'Technical Analysis: SMA'
        data = self.translate(raw_response, key)
        return data

    def get_rsi_response(self):
        indicator_key = self.get_indicator_key()  # e.g. BTCUSD
        query = {
            "apikey": self.api_key,
            "symbol": indicator_key,
            "function": "RSI",
            "interval": self.get_argument_value(ArgumentType.INTERVAL).value,
            "time_period": int(self.get_argument_value(ArgumentType.RSI_PERIOD)),
            "series_type": "close"
        }
        raw_response, data_file = self.get_url_response(self.url, query)
        self.validate_json_response(data_file, raw_response)
        key = 'Technical Analysis: RSI'
        self.translate(raw_response, key)

    def get_earnings_response(self):
        interval: TimeInterval = self.get_argument_value(ArgumentType.INTERVAL)
        query = {
            "apikey": self.api_key,
            "symbol": self.symbol,
            "function": "EARNINGS",
            # "interval": interval.value,
        }
        raw_response, data_file = self.get_url_response(self.url, query)
        if interval == TimeInterval.YEAR:
            key = 'annualEarnings'
        elif interval == TimeInterval.QUARTER:
            key = 'quarterlyEarnings'
        else:
            raise RuntimeError(
                'Interval not supported: {} (for: {})'.format(interval, self.__class__.__name__))
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
            self.insert_data_column(converter.value_type, indexes, values)

    def get_income_response(self):
        interval: TimeInterval = self.get_argument_value(ArgumentType.INTERVAL)
        query = {
            "apikey": self.api_key,
            "symbol": self.symbol,
            "function": "INCOME_STATEMENT",
            # "interval": interval.value,
        }
        raw_response, data_file = self.get_url_response(self.url, query)
        if interval == TimeInterval.YEAR:
            key = 'annualReports'
        elif interval == TimeInterval.QUARTER:
            key = 'quarterlyReports'
        else:
            raise RuntimeError(
                'Interval is not supported: {} (for: {})'.format(interval, self.__class__.__name__))
        self.translate_earnings(raw_response, key)
        # self.translate_income(raw_response, key)

    def translate_income(self, response_data, key, data_date_format='%Y-%m-%d'):
        if key not in response_data:
            raise RuntimeError("Failed to find key in data: {}".format(key))
        if not response_data[key]:
            raise RuntimeError(
                "There is no data (length is 0) for key: {} (maybe try a different time interval)".format(key))
        translated = {}
        for entry in response_data[key]:
            dt = datetime.strptime(entry['fiscalDateEnding'], data_date_format)
            translated[dt] = {}
            for value_type in ValueType:
                value = self.get_response_value_or_none(entry, value_type)
                if value is not None:
                    ratio = self.get_adjusted_ratio(entry)
                    value = value * ratio
                    translated[dt][value_type] = value
        return translated

    def get_balance_sheet_response(self):
        interval: TimeInterval = self.get_argument_value(ArgumentType.INTERVAL)
        query = {
            "apikey": self.api_key,
            "symbol": self.symbol,
            "function": "BALANCE_SHEET",
            # "interval": interval.value,
        }
        raw_response, data_file = self.get_url_response(self.url, query)
        if interval == TimeInterval.YEAR:
            key = 'annualReports'
        elif interval == TimeInterval.QUARTER:
            key = 'quarterlyReports'
        else:
            raise RuntimeError(
                'Interval is not supported: {} (for: {})'.format(interval, self.__class__.__name__))
        self.translate_earnings(raw_response, key)
        # self.translate_balance_sheet(raw_response, key)

    def translate_balance_sheet(self, response_data, key, data_date_format='%Y-%m-%d'):
        if key not in response_data:
            raise RuntimeError("Failed to find key in data: {}".format(key))
        if not response_data[key]:
            raise RuntimeError(
                "There is no data (length is 0) for key: {} (maybe try a different time interval)".format(key))
        translated = {}
        for entry in response_data[key]:
            dt = datetime.strptime(entry['fiscalDateEnding'], data_date_format)
            translated[dt] = {}
            for value_type in ValueType:
                value = self.get_response_value_or_none(entry, value_type)
                if value is not None:
                    ratio = self.get_adjusted_ratio(entry)
                    value = value * ratio
                    translated[dt][value_type] = value
        return translated

    def get_cash_flow_response(self):
        interval: TimeInterval = self.get_argument_value(ArgumentType.INTERVAL)
        query = {
            "apikey": self.api_key,
            "symbol": self.symbol,
            "function": "CASH_FLOW",
            # "interval": interval.value,
        }
        raw_response, data_file = self.get_url_response(self.url, query)
        if interval == TimeInterval.YEAR:
            key = 'annualReports'
        elif interval == TimeInterval.QUARTER:
            key = 'quarterlyReports'
        else:
            raise RuntimeError(
                'Interval is not supported: {} (for: {})'.format(interval, self.__class__.__name__))
        self.translate_earnings(raw_response, key)
        # self.translate_cash_flow(raw_response, key)

    def translate_cash_flow(self, response_data, key, data_date_format='%Y-%m-%d'):
        if key not in response_data:
            raise RuntimeError("Failed to find key in data: {}".format(key))
        if not response_data[key]:
            raise RuntimeError(
                "There is no data (length is 0) for key: {} (maybe try a different time interval)".format(key))
        translated = {}
        for entry in response_data[key]:
            dt = datetime.strptime(entry['fiscalDateEnding'], data_date_format)
            translated[dt] = {}
            for value_type in ValueType:
                value = self.get_response_value_or_none(entry, value_type)
                if value is not None:
                    ratio = self.get_adjusted_ratio(entry)
                    value = value * ratio
                    translated[dt][value_type] = value
        return translated

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
                buffer = 10
                sleep_in_s = buffer + sleep.seconds + sleep.microseconds / 1000000.0
                logging.info('-- Waiting for: {} = closest:{} - now:{}'.format(sleep_in_s, closest, now))
                # logging.info('MAP: {}'.format(json.dumps(self.historicRequests, indent=2, default=str)))
                time.sleep(sleep_in_s)
            else:
                wait = False

    def get_create_times(self):
        cache_requests = {}
        date_dir = os.path.join(self.cache_dir, self.cache_key_date.strftime('%Y%m%d'))
        for filename in os.listdir(date_dir):
            file_path = os.path.join(date_dir, filename)
            if filename.startswith(".lock"):
                continue
            cache_requests[file_path] = datetime.fromtimestamp(os.stat(file_path).st_ctime)
            # modTimesinceEpoc = os.path.getmtime(file_path)
        return cache_requests

    def get_is_digital_currency(self):
        data, data_file = self.get_url_response("https://www.alphavantage.co/digital_currency_list", {},
                                                cache=True, data_type=DataType.CSV, delay=False)
        data = data[1:]  # remove header
        data = [item[0] for item in data]
        return self.symbol in data

    def get_is_listed(self) -> bool:
        data = self.get_equities_list()
        return self.symbol in data

    def get_is_physical_currency(self):
        data, data_file = self.get_url_response("https://www.alphavantage.co/physical_currency_list", {},
                                                cache=True, data_type=DataType.CSV, delay=False)
        data = data[1:]  # remove header
        data = [item[0] for item in data]
        return self.base_symbol in data
