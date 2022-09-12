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

# Start here:
#  https://developer.tdameritrade.com/content/authentication-faq

from datetime import datetime, timedelta
from os import environ
from typing import Dict, List, Optional

from main.application.adapter import DataType, AssetType, Adapter, get_response_value_or_none, \
    IntervalNotSupportedException, insert_column, request_limit_with_timedelta_delay
from main.application.argument import ArgumentKey
from main.application.converter import Converter
from main.application.time_interval import TimeInterval
from main.application.value_type import ValueType
from main.common.locations import file_link_format


def get_adjusted_ratio(time_data: Dict[str, str]) -> float:
    """
    TDA provides the stock values as they were and an adjusted close value. This is to
    account for stock splits. To fix these close/adjusted_close = ratio and then ratio * price to
    get the correct price to account for current splits etc.
    :param time_data:
    :return:
    """
    adjusted_close = get_response_value_or_none(time_data, '5. adjusted close')
    # adjusted_close = self.get_value_or_none(time_data, ValueType.ADJUSTED_CLOSE)
    close = get_response_value_or_none(time_data, '4. close')
    ratio = 1.0 if (adjusted_close is None) or (close is None) else adjusted_close / close
    return float(ratio)


# def find_symbol_in_data(data, entry):
#     contains = False
#     for row in data:
#         if row[0] == entry:
#             contains = True
#             break
#     return contains


class TDA(Adapter):
    name: str = 'tda'
    # NOTE: https://api.tdameritrade.com/v1/marketdata/{symbol}/pricehistory
    url: str = 'https://api.tdameritrade.com/v1/marketdata/'

    def __init__(self, symbol: str, asset_type: Optional[AssetType] = None):
        if environ.get('ALPHA_VANTAGE_API_KEY') is None:
            raise RuntimeError(
                "The ALPHA_VANTAGE_API_KEY environment variable is not set - this needs to be set to the API KEY for "
                "your account from the alphavantage.co site.")
        api_key = environ.get('ALPHA_VANTAGE_API_KEY')
        super().__init__(symbol, asset_type)
        self.api_key = api_key
        # script_dir = os.path.dirname(os.path.realpath(__file__))
        # cache_dir = os.path.join(script_dir, '..', '..', '..', '..', '.cache', TDA.name)
        # self.cache_root_dir = os.path.realpath(cache_dir)
        self.converters: List[Converter] = [
            # we allow for multiple strings to be converted into the value type, first match is used
            Converter(ValueType.OPEN, self.get_prices_response, ['1. open', '1a. open (USD)'], adjust_values=True),
            Converter(ValueType.HIGH, self.get_prices_response, ['2. high', '2a. high (USD)'], adjust_values=True),
            Converter(ValueType.LOW, self.get_prices_response, ['3. low', '3a. low (USD)'], adjust_values=True),
            Converter(ValueType.CLOSE, self.get_prices_response, ['4. close', '4a. close (USD)'],
                      adjust_values=True),
            Converter(ValueType.VOLUME, self.get_prices_response, ['5. volume']),
            Converter(ValueType.RSI, self.get_rsi_response, ['RSI']),
            Converter(ValueType.MACD, self.get_macd_response, ['MACD']),
            Converter(ValueType.MACD_HIST, self.get_macd_response, ['MACD_Hist']),
            Converter(ValueType.MACD_SIGNAL, self.get_macd_response, ['MACD_Signal']),
            Converter(ValueType.SMA, self.get_sma_response, ['SMA']),
            Converter(ValueType.EPS, self.get_earnings_response, ['reportedEPS']),
            Converter(ValueType.REVENUE, self.get_income_response, ['totalRevenue']),
            # ESTIMATED_EPS = auto()
            # SURPRISE_EPS = auto()
            # SURPRISE_PERCENTAGE_EPS = auto()
            # GROSS_PROFIT = auto()
            # TOTAL_REVENUE = auto()
            # OPERATING_CASH_FLOW = auto()
            # Converter(ValueType.DEPRECIATION, self.get_cash_flow_response, ['depreciationDepletionAndAmortization']),
            # Converter(ValueType.RECEIVABLES, self.get_cash_flow_response, ['changeInReceivables']),
            # Converter(ValueType.INVENTORY, self.get_cash_flow_response, ['changeInInventory']),
            # Converter(ValueType.PAYABLES, self.get_cash_flow_response, ['operatingCashflow']),
            # Converter(ValueType.CAPITAL_EXPENDITURES, self.get_cash_flow_response, ['capitalExpenditures']),
            # Converter(ValueType.FREE_CASH_FLOW, self.get_cash_flow_response, ['operatingCashflow']),

            Converter(ValueType.CASH_FLOW, self.get_cash_flow_response, ['operatingCashflow']),
            Converter(ValueType.DIVIDENDS, self.get_cash_flow_response, ['dividendPayout']),
            Converter(ValueType.NET_INCOME, self.get_cash_flow_response, ['netIncome']),
            Converter(ValueType.ASSETS, self.get_balance_sheet_response, ['totalAssets']),
            Converter(ValueType.LIABILITIES, self.get_balance_sheet_response, ['totalLiabilities']),
            Converter(ValueType.SHORT_DEBT, self.get_balance_sheet_response, ['shortTermDebt']),
            Converter(ValueType.LONG_DEBT, self.get_balance_sheet_response, ['longTermDebt']),
            # This value was very wrong for BRK-A, it says something like 3687360528 shares outstanding, while there
            # are actually only something like 640000
            Converter(ValueType.SHARES, self.get_balance_sheet_response, ['commonStockSharesOutstanding']),
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
            Converter(ValueType.EQUITY, self.get_balance_sheet_response, ['totalShareholderEquity']),
        ]

    def get_equities_list(self) -> List[str]:
        query = {
            "apikey":   self.api_key,
            "function": "LISTING_STATUS",
        }
        data, data_file = self.get_url_response(self.url, query, cache=True, data_type=DataType.CSV)
        data = data[1:]  # remove header
        data = [item[0] for item in data]
        return data

    def get_prices_response(self, value_type: ValueType) -> None:
        if self.asset_type is AssetType.DIGITAL_CURRENCY:
            self.get_digital_currency_response(value_type)
        else:
            self.get_stock_prices_response(value_type)

    def get_stock_prices_response(self, value_type: ValueType) -> None:
        query = {
            "apikey": self.api_key,
            "symbol": self.symbol
        }
        interval: TimeInterval = self.get_argument_value(ArgumentKey.INTERVAL)
        end_time: Optional[datetime] = self.get_argument_value(ArgumentKey.END_TIME)
        end_time = datetime.now() if end_time is None else end_time
        start_time: Optional[datetime] = self.get_argument_value(ArgumentKey.START_TIME)
        start_time = end_time - timedelta(days=1) if start_time is None else start_time
        record_count = (end_time - start_time) / interval.timedelta
        output_size = "compact" if record_count < 100 else "full"
        if interval == TimeInterval.HOUR:
            query["function"] = "TIME_SERIES_INTRADAY"
            query["interval"] = '60min'
            query["adjusted"] = True
            query["outputsize"] = output_size
            key = 'Time Series (60min)'
        elif interval == TimeInterval.DAY:
            query["function"] = "TIME_SERIES_DAILY_ADJUSTED"
            query["outputsize"] = output_size
            key = 'Time Series (Daily)'
        elif interval == TimeInterval.WEEK:
            query["function"] = "TIME_SERIES_WEEKLY_ADJUSTED"
            key = 'Weekly Adjusted Time Series'
        elif interval == TimeInterval.MONTH:
            query["function"] = "TIME_SERIES_MONTHLY_ADJUSTED"
            key = 'Monthly Adjusted Time Series'
        else:
            raise IntervalNotSupportedException(f"Specified interval is not supported: '{interval}' "
                                                f"(for: {self.__class__.__name__})")
        raw_response, data_file = self.get_url_response(self.url, query)
        self.validate_json_response(data_file, raw_response)
        self.translate(raw_response, value_type, key)

    def get_digital_currency_response(self, value_type: ValueType) -> None:
        query = {
            "apikey": self.api_key,
            "symbol": self.symbol,
            "market": self.base_symbol
        }
        interval: TimeInterval = self.get_argument_value(ArgumentKey.INTERVAL)
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
        self.translate(raw_response, value_type, key)

    def translate(self, response_data, value_type: ValueType, key, data_date_format='%Y-%m-%d') -> None:
        """
        This method converts the raw data returned from rest API calls into
        :param response_data: Data from an API or URL request (raw data generally JSON, CSV, etc.)
        :param value_type: The value type we will be converting and the column we will be inserting
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
            if converter.value_type != value_type:
                continue
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
                    ratio = get_adjusted_ratio(response_entry)
                    value = value * ratio
                indexes.append(datetime.fromisoformat(entry_datetime))
                values.append(value)
            insert_column(self.data, converter.value_type, indexes, values)

    def get_macd_response(self, value_type: ValueType) -> None:
        indicator_key = self.get_indicator_key()  # e.g. BTCUSD
        query = {
            "apikey":       self.api_key,
            "symbol":       indicator_key,
            "function":     "MACD",
            "interval":     self.get_argument_value(ArgumentKey.INTERVAL).value,
            "slowperiod":   int(self.get_argument_value(ArgumentKey.MACD_SLOW)),
            "fastperiod":   int(self.get_argument_value(ArgumentKey.MACD_FAST)),
            "signalperiod": int(self.get_argument_value(ArgumentKey.MACD_SIGNAL)),
            "series_type":  "close"
        }
        raw_response, data_file = self.get_url_response(self.url, query)
        self.validate_json_response(data_file, raw_response)
        self.translate(raw_response, value_type, 'Technical Analysis: MACD')

    def get_sma_response(self, value_type: ValueType):
        indicator_key = self.get_indicator_key()  # e.g. BTCUSD
        query = {
            "apikey":      self.api_key,
            "symbol":      indicator_key,
            "function":    "SMA",
            "interval":    self.get_argument_value(ArgumentKey.INTERVAL).value,
            "time_period": int(self.get_argument_value(ArgumentKey.SMA_PERIOD)),
            "series_type": "close",
        }
        raw_response, data_file = self.get_url_response(self.url, query)
        self.validate_json_response(data_file, raw_response)
        self.translate(raw_response, value_type, 'Technical Analysis: SMA')

    def get_rsi_response(self, value_type: ValueType):
        indicator_key = self.get_indicator_key()  # e.g. BTCUSD
        query = {
            "apikey":      self.api_key,
            "symbol":      indicator_key,
            "function":    "RSI",
            "interval":    self.get_argument_value(ArgumentKey.INTERVAL).value,
            "time_period": int(self.get_argument_value(ArgumentKey.RSI_PERIOD)),
            "series_type": "close"
        }
        raw_response, data_file = self.get_url_response(self.url, query)
        self.validate_json_response(data_file, raw_response)
        key = 'Technical Analysis: RSI'
        self.translate(raw_response, value_type, key)

    def get_earnings_response(self, value_type: ValueType):
        interval: TimeInterval = self.get_argument_value(ArgumentKey.INTERVAL)
        query = {
            "apikey":   self.api_key,
            "symbol":   self.symbol,
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
        self.validate_json_response(data_file, raw_response, expects_meta_data=False)
        self.translate_earnings(raw_response, value_type, key)

    def translate_earnings(self, response_data, value_type: ValueType, key, data_date_format='%Y-%m-%d'):
        if key not in response_data:
            raise RuntimeError("Failed to find key in data: {}".format(key))
        if not response_data[key]:
            raise RuntimeError(
                "There is no data (length is 0) for key: {} (maybe try a different time interval)".format(key))
        for converter in self.converters:
            if converter.value_type in self.data:
                continue  # if we've already added this value type, then don't do it again
            if converter.value_type != value_type:
                continue
            indexes = []
            values = []
            for entry in response_data[key]:
                value = None
                for response_key, response_value in entry.items():
                    if response_key in converter.response_keys:
                        value = 0.0 if response_value == 'None' else float(response_value)
                        break
                if value is not None:
                    indexes.append(datetime.fromisoformat(entry['fiscalDateEnding']))
                    values.append(value)
            insert_column(self.data, converter.value_type, indexes, values)
        assert value_type in self.data, "Parsing response data failed, was adding column for value type '{}', but " \
                                        "no data was present after getting and parsing the response. Does the " \
                                        "converter have the correct keys/locations for the raw data?".format(value_type)

    def get_income_response(self, value_type: ValueType) -> None:
        interval: TimeInterval = self.get_argument_value(ArgumentKey.INTERVAL)
        query = {
            "apikey":   self.api_key,
            "symbol":   self.symbol,
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
        self.validate_json_response(data_file, raw_response, expects_meta_data=False)
        self.translate_earnings(raw_response, value_type, key)
        # self.translate_income(raw_response, value_type, key)

    def translate_income(self, response_data, key, data_date_format='%Y-%m-%d') -> Dict[datetime, Dict]:
        if key not in response_data:
            raise RuntimeError("Failed to find key in data: {}".format(key))
        if not response_data[key]:
            raise RuntimeError(
                "There is no data (length is 0) for key: {} (maybe try a different time interval)".format(key))
        translated = {}
        for entry in response_data[key]:
            dt = datetime.fromisoformat(entry['fiscalDateEnding'])
            translated[dt] = {}
            for value_type in ValueType:
                value = get_response_value_or_none(entry, value_type)
                if value is not None:
                    ratio = get_adjusted_ratio(entry)
                    value = value * ratio
                    translated[dt][value_type] = value
        return translated

    def get_balance_sheet_response(self, value_type: ValueType):
        interval: TimeInterval = self.get_argument_value(ArgumentKey.INTERVAL)
        query = {
            "apikey":   self.api_key,
            "symbol":   self.symbol,
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
        self.translate_earnings(raw_response, value_type, key)
        # self.translate_balance_sheet(raw_response, value_type, key)

    def translate_balance_sheet(self, response_data, key, data_date_format='%Y-%m-%d'):
        if key not in response_data:
            raise RuntimeError("Failed to find key in data: {}".format(key))
        if not response_data[key]:
            raise RuntimeError(
                "There is no data (length is 0) for key: {} (maybe try a different time interval)".format(key))
        translated = {}
        for entry in response_data[key]:
            dt = datetime.fromisoformat(entry['fiscalDateEnding'])
            translated[dt] = {}
            for value_type in ValueType:
                value = get_response_value_or_none(entry, value_type)
                if value is not None:
                    ratio = get_adjusted_ratio(entry)
                    value = value * ratio
                    translated[dt][value_type] = value
        return translated

    def get_cash_flow_response(self, value_type: ValueType):
        interval: TimeInterval = self.get_argument_value(ArgumentKey.INTERVAL)
        query = {
            "apikey":   self.api_key,
            "symbol":   self.symbol,
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
        self.translate_earnings(raw_response, value_type, key)
        # self.translate_cash_flow(raw_response, value_type, key)

    def translate_cash_flow(self, response_data, key, data_date_format='%Y-%m-%d'):
        if key not in response_data:
            raise RuntimeError("Failed to find key in data: {}".format(key))
        if not response_data[key]:
            raise RuntimeError(
                "There is no data (length is 0) for key: {} (maybe try a different time interval)".format(key))
        translated = {}
        for entry in response_data[key]:
            dt = datetime.fromisoformat(entry['fiscalDateEnding'])
            translated[dt] = {}
            for value_type in ValueType:
                value = get_response_value_or_none(entry, value_type)
                if value is not None:
                    ratio = get_adjusted_ratio(entry)
                    value = value * ratio
                    translated[dt][value_type] = value
        return translated

    @staticmethod
    def validate_json_response(data_file, raw_response, expects_meta_data=True):
        if "Error Message" in raw_response:
            raise RuntimeError(
                "Error message in response - {}\n  See: {}".format(raw_response["Error Message"],
                                                                   file_link_format(data_file)))
        if "Note" in raw_response:
            raise RuntimeError("Note message in response - {}\n  See: {}".format(raw_response["Note"],
                                                                                 file_link_format(data_file)))
        if expects_meta_data and "Meta Data" not in raw_response:
            raise RuntimeError("Failed to find the meta data in response: {} (perhaps the currency doesn't support "
                               "this)".format(file_link_format(data_file)))

    def get_indicator_key(self):
        self.calculate_asset_type()
        indicator_key = self.symbol
        if self.asset_type == AssetType.DIGITAL_CURRENCY:
            indicator_key = self.symbol + self.base_symbol  # e.g. BTCUSD
        return indicator_key

    def delay_requests(self, data_file: str) -> None:
        request_limit_with_timedelta_delay(buffer=10, historic_requests=self.get_create_times(),
                                           max_timeframe=timedelta(minutes=1), max_requests=5)

    def get_is_digital_currency(self):
        data, data_file = self.get_url_response("https://www.alphavantage.co/digital_currency_list", {},
                                                cache=True, data_type=DataType.CSV, delay=False)
        data = data[1:]  # remove header
        data = [item[0] for item in data]
        return self.symbol in data

    def get_is_stock(self) -> bool:
        data = self.get_equities_list()
        return self.symbol in data

    def get_is_physical_currency(self):
        data, data_file = self.get_url_response("https://www.alphavantage.co/physical_currency_list", {},
                                                cache=True, data_type=DataType.CSV, delay=False)
        data = data[1:]  # remove header
        data = [item[0] for item in data]
        return self.base_symbol in data
