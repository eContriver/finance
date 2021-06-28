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
from typing import Optional

from main.adapters.adapter import DataType, TimeInterval, AssetType
from main.adapters.valueType import ValueType
from main.adapters.fundamentals.balanceSheet import BalanceSheet
from main.adapters.fundamentals.cashFlow import CashFlow
from main.adapters.fundamentals.earnings import Earnings
from main.adapters.fundamentals.income import Income
from main.adapters.indicators.macd import Macd
from main.adapters.indicators.rsi import Rsi
from main.adapters.indicators.series import Series
from main.adapters.indicators.sma import Sma


class FinancialModelingPrep(
    Series,
    # Rsi,
    # Macd,
    # Sma,
    # Earnings,
    # Income,
    # BalanceSheet,
    # CashFlow,
):
    name: str = 'financialModelingPrep'
    url: str = 'https://financialmodelingprep.com/api/v3'

    def __init__(self, symbol: str, base_symbol: str = 'USD',
                 cache_key_date: Optional[datetime] = None, span: Optional[timedelta] = None):
        if environ.get('FMP_API_KEY') is None:
            raise RuntimeError(
                "The FMP_API_KEY environment variable is not set - this needs to be set to the API KEY for "
                "your account from the site: https://financialmodelingprep.com/developer/docs/dashboard/")
        api_key = environ.get('FMP_API_KEY')
        super().__init__(symbol, base_symbol, cache_key_date, span)
        self.api_key = api_key
        script_dir = os.path.dirname(os.path.realpath(__file__))
        cache_dir = os.path.join(script_dir, '../..', '..', '..', '.cache', FinancialModelingPrep.name)
        self.cache_dir = os.path.realpath(cache_dir)

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
        data, data_file = self.get_url_response("{}/{}".format(FinancialModelingPrep.url, 'query'), query, cache=True,
                                                data_type=DataType.CSV)
        data = data[1:]  # remove header
        data = [item[0] for item in data]
        return data

    def get_stock_series_response(self):
        query = {}
        query["apikey"] = self.api_key
        query["symbol"] = self.symbol
        data_date_format = '%Y-%m-%d'
        if self.series_interval == TimeInterval.HOUR:
            query["function"] = "TIME_SERIES_INTRADAY"
            query["interval"] = TimeInterval.HOUR.value
            query["adjusted"] = True
            query["outputsize"] = "full"
            key = 'Time Series (60min)'
            data_date_format = '%Y-%m-%d %H:%M:%S'
        elif self.series_interval == TimeInterval.DAY:
            query["function"] = "TIME_SERIES_DAILY_ADJUSTED"
            query["outputsize"] = "full"
            key = 'Time Series (Daily)'
        elif self.series_interval == TimeInterval.WEEK:
            query["function"] = "TIME_SERIES_WEEKLY_ADJUSTED"
            key = 'Weekly Adjusted Time Series'
        elif self.series_interval == TimeInterval.MONTH:
            query["function"] = "TIME_SERIES_MONTHLY_ADJUSTED"
            key = 'Monthly Adjusted Time Series'
        else:
            raise RuntimeError(
                'Interval is not supported: {} (for: {})'.format(self.series_interval, self.__class__.__name__))
        raw_response, data_file = self.get_url_response("{}/{}".format(FinancialModelingPrep.url, 'query'), query)
        data = self.translate(raw_response, key)
        return data

    def translate(self, response_data, key, data_date_format='%Y-%m-%d'):
        if key not in response_data:
            raise RuntimeError("Failed to find key in data: {}".format(key))
        if not response_data[key]:
            raise RuntimeError(
                "There is no data (length is 0) for key: {} (maybe try a different time interval)".format(key))
        translated = {}
        for period, entry in response_data[key].items():
            dt = datetime.strptime(period, data_date_format)
            translated[dt] = {}
            for seriesType in ValueType:
                value = self.get_value_or_none(entry, seriesType)
                if value is not None:
                    ratio = self.get_adjusted_ratio(entry)
                    value = value * ratio
                    translated[dt][seriesType] = value
        return translated

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
            "apikey": self.api_key,
            "function": function,
            "symbol": self.symbol,
            "market": self.base_symbol,
        }
        raw_response, data_file = self.get_url_response("{}/{}".format(FinancialModelingPrep.url, 'query'), query)
        self.validate_json_response(data_file, raw_response)
        data = self.translate(raw_response, key)
        return data

    def get_macd_response(self):
        indicator_key = self.get_indicator_key()  # e.g. BTCUSD
        query = {
            "apikey": self.api_key,
            "function": "MACD",
            "symbol": indicator_key,
            "interval": self.macd_interval.value,
            "slowperiod": int(self.macd_slow_period),
            "fastperiod": int(self.macd_fast_period),
            "signalperiod": int(self.macd_signal_period),
            "series_type": self.macd_series_type.value,
        }
        raw_response, data_file = self.get_url_response("{}/{}".format(FinancialModelingPrep.url, 'query'), query)
        self.validate_json_response(data_file, raw_response)
        data = self.translate(raw_response, 'Technical Analysis: MACD')
        return data

    def get_sma_response(self):
        indicator_key = self.get_indicator_key()  # e.g. BTCUSD
        query = {
            "apikey": self.api_key,
            "function": "SMA",
            "symbol": indicator_key,
            "interval": self.sma_interval.value,
            "time_period": self.sma_period,
            "series_type": self.sma_series_type,
        }
        raw_response, data_file = self.get_url_response("{}/{}".format(FinancialModelingPrep.url, 'query'), query)
        self.validate_json_response(data_file, raw_response)
        key = 'Technical Analysis: SMA'
        data = self.translate(raw_response, key)
        return data

    def get_rsi_response(self):
        indicator_key = self.get_indicator_key()  # e.g. BTCUSD
        query = {
            "apikey": self.api_key,
            "function": "RSI",
            "symbol": indicator_key,
            "interval": self.rsi_interval.value,
            "time_period": int(self.rsi_period),
            "series_type": self.rsi_series_type.value,
        }
        raw_response, data_file = self.get_url_response("{}/{}".format(FinancialModelingPrep.url, 'query'), query)
        self.validate_json_response(data_file, raw_response)
        key = 'Technical Analysis: RSI'
        data = self.translate(raw_response, key)
        return data

    def get_earnings_response(self):
        query = {}
        query["apikey"] = self.api_key
        query["symbol"] = self.symbol
        query["function"] = "EARNINGS"
        raw_response, data_file = self.get_url_response("{}/{}".format(FinancialModelingPrep.url, 'query'), query)
        interval = self.earnings_interval
        if interval == TimeInterval.YEAR:
            key = 'annualEarnings'
        elif interval == TimeInterval.QUARTER:
            key = 'quarterlyEarnings'
        else:
            raise RuntimeError(
                'Interval is not supported: {} (for: {})'.format(interval, self.__class__.__name__))
        data = self.translate_earnings(raw_response, key)
        return data

    def translate_earnings(self, response_data, key, data_date_format='%Y-%m-%d'):
        if key not in response_data:
            raise RuntimeError("Failed to find key in data: {}".format(key))
        if not response_data[key]:
            raise RuntimeError(
                "There is no data (length is 0) for key: {} (maybe try a different time interval)".format(key))
        translated = {}
        for entry in response_data[key]:
            dt = datetime.strptime(entry['fiscalDateEnding'], data_date_format)
            translated[dt] = {}
            for seriesType in ValueType:
                value = self.get_value_or_none(entry, seriesType)
                if value is not None:
                    ratio = self.get_adjusted_ratio(entry)
                    value = value * ratio
                    translated[dt][seriesType] = value
        return translated

    def get_income_response(self):
        query = {}
        query["apikey"] = self.api_key
        query["symbol"] = self.symbol
        query["function"] = "INCOME_STATEMENT"
        raw_response, data_file = self.get_url_response("{}/{}".format(FinancialModelingPrep.url, 'query'), query)
        interval = self.income_interval
        if interval == TimeInterval.YEAR:
            key = 'annualReports'
        elif interval == TimeInterval.QUARTER:
            key = 'quarterlyReports'
        else:
            raise RuntimeError(
                'Interval is not supported: {} (for: {})'.format(interval, self.__class__.__name__))
        data = self.translate_income(raw_response, key)
        return data

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
            for seriesType in ValueType:
                value = self.get_value_or_none(entry, seriesType)
                if value is not None:
                    ratio = self.get_adjusted_ratio(entry)
                    value = value * ratio
                    translated[dt][seriesType] = value
        return translated

    def get_balance_sheet_response(self):
        query = {}
        query["apikey"] = self.api_key
        query["symbol"] = self.symbol
        query["function"] = "BALANCE_SHEET"
        raw_response, data_file = self.get_url_response("{}/{}".format(FinancialModelingPrep.url, 'query'), query)
        interval = self.balance_sheet_interval
        if interval == TimeInterval.YEAR:
            key = 'annualReports'
        elif interval == TimeInterval.QUARTER:
            key = 'quarterlyReports'
        else:
            raise RuntimeError(
                'Interval is not supported: {} (for: {})'.format(interval, self.__class__.__name__))
        data = self.translate_balance_sheet(raw_response, key)
        return data

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
            for seriesType in ValueType:
                value = self.get_value_or_none(entry, seriesType)
                if value is not None:
                    ratio = self.get_adjusted_ratio(entry)
                    value = value * ratio
                    translated[dt][seriesType] = value
        return translated

    def get_cash_flow_response(self):
        query = {}
        query["apikey"] = self.api_key
        query["symbol"] = self.symbol
        query["function"] = "CASH_FLOW"
        raw_response, data_file = self.get_url_response("{}/{}".format(FinancialModelingPrep.url, 'query'), query)
        interval = self.cash_flow_interval
        if interval == TimeInterval.YEAR:
            key = 'annualReports'
        elif interval == TimeInterval.QUARTER:
            key = 'quarterlyReports'
        else:
            raise RuntimeError(
                'Interval is not supported: {} (for: {})'.format(interval, self.__class__.__name__))
        data = self.translate_cash_flow(raw_response, key)
        return data

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
            for seriesType in ValueType:
                value = self.get_value_or_none(entry, seriesType)
                if value is not None:
                    ratio = self.get_adjusted_ratio(entry)
                    value = value * ratio
                    translated[dt][seriesType] = value
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
        query = {}
        query["apikey"] = self.api_key
        data, data_file = self.get_url_response(
            "{}/{}".format(FinancialModelingPrep.url, 'symbol/available-cryptocurrencies'), query)
        data = data[1:]  # remove header
        data = [item[0] for item in data]
        return self.symbol in data

    def get_is_listed(self) -> bool:
        data = self.get_equities_list()
        return self.symbol in data

    def get_is_physical_currency(self):
        data, data_file = self.get_url_response("{}/{}".format(FinancialModelingPrep.url, 'physical_currency_list'), {},
                                                cache=True, data_type=DataType.CSV)
        data = data[1:]  # remove header
        data = [item[0] for item in data]
        return self.base_symbol in data
