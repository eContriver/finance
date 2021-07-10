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
from main.adapters.indicators.series import Series


class Sec(Series,
          # Rsi,
          # Macd,
          # Sma,
          Earnings,
          Income,
          BalanceSheet,
          CashFlow,
          ):
    name: str = 'sec'
    url: str = 'https://www.sec.gov'

    def __init__(self, symbol: str, base_symbol: str = 'USD',
                 cache_key_date: Optional[datetime] = None, span: Optional[timedelta] = None):
        super().__init__(symbol, base_symbol, cache_key_date, span)
        script_dir = os.path.dirname(os.path.realpath(__file__))
        cache_dir = os.path.join(script_dir, '..', '..', '..', '..', '.cache', Sec.name)
        self.cache_dir = os.path.realpath(cache_dir)
        self.value_type_map[ValueType.DIVIDENDS] = "dividendsPaid"

    def delay_requests(self, data_file):
        wait = True
        max_requests = 10
        per_time_unit = timedelta(seconds=1)
        while wait:
            # NOTE: there is a race condition here if running multi-process...
            #       files could be created between when you read their create times and return thus allowing more than
            #       X (i.e. 10 for this adapter) requests per allotted timeframe (i.e. minute for this)
            #       to fix this you could create yet another lock here, but for now we limit to 1 request at a time
            #       and that elegantly fixes this as well as prevents us from hammering servers ;)
            historic_requests: dict = self.get_create_times()
            wait_list = []
            now: datetime = datetime.now()
            closest = now + per_time_unit
            for key, request_time in historic_requests.items():
                reset_time = request_time + per_time_unit
                if reset_time > now:
                    wait_list.append(key)
                    if reset_time < closest:
                        closest = reset_time
            if len(wait_list) >= max_requests:
                sleep = closest - now
                buffer_in_s = 10.0 / 1000.0  # use a 10ms buffer
                sleep_in_s = buffer_in_s + sleep.seconds + sleep.microseconds / 1000000.0
                logging.info('-- Waiting for: {} = closest:{} - now:{}'.format(sleep_in_s, closest, now))
                # logging.info('MAP: {}'.format(json.dumps(self.historicRequests, indent=2, default=str)))
                time.sleep(sleep_in_s)
            else:
                wait = False

    def find_symbol_in_data(self, data, entry):
        contains = False
        for row in data:
            if row[0] == entry:
                contains = True
                break
        return contains

    def get_equities_list(self):
        # To list cik + ticket + name
        # https://www.sec.gov/files/company_tickers.json
        # To list cik + ticket + name + exchange
        # https://www.sec.gov/files/company_tickers_exchange.json
        query = {
        }
        data, data_file = self.get_url_response('{}/files/company_tickers.json'.format(self.url), query)
        data = [item['ticker'] for item in data.values()]
        return data

    def get_stock_series_response(self):
        query = {
        }
        if self.span <= TimeInterval.DAY.timedelta:
            # if self.series_interval == TimeInterval.DAY:
            series_range = '1d'
        elif self.span <= TimeInterval.WEEK.timedelta:
            # elif self.series_interval == TimeInterval.WEEK:
            series_range = '1w'
        elif self.span <= TimeInterval.MONTH.timedelta:
            series_range = '1m'
        elif self.span <= TimeInterval.QUARTER.timedelta:
            series_range = '3m'
        elif self.span <= TimeInterval.YEAR.timedelta:
            series_range = '1y'
        elif self.span <= TimeInterval.YEAR2.timedelta:
            series_range = '2y'
        elif self.span <= TimeInterval.YEAR5.timedelta:
            series_range = '5y'
        else:
            series_range = 'max'
        raw_response, data_file = self.get_url_response('{}/stock/{}/chart/{}'.format(self.url,
                                                                                      self.symbol,
                                                                                      series_range),
                                                        query)
        data = self.translate(raw_response)
        return data

    def translate(self, response_data, data_date_format='%Y-%m-%d'):
        if not response_data:
            raise RuntimeError("There is no data (length is 0) for (maybe try a different time interval)")
        translated = {}
        for entry in response_data:
            dt = datetime.strptime(entry['date'], data_date_format)
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
            "function": function,
            "symbol": self.symbol,
            "market": self.base_symbol,
        }
        raw_response, data_file = self.get_url_response(self.url, query)
        self.validate_json_response(data_file, raw_response)
        data = self.translate(raw_response, key)
        return data

    def get_macd_response(self):
        indicator_key = self.get_indicator_key()  # e.g. BTCUSD
        query = {
            "function": "MACD",
            "symbol": indicator_key,
            "interval": self.macd_interval.value,
            "slowperiod": int(self.macd_slow_period),
            "fastperiod": int(self.macd_fast_period),
            "signalperiod": int(self.macd_signal_period),
            "series_type": self.macd_series_type.value,
        }
        raw_response, data_file = self.get_url_response(self.url, query)
        self.validate_json_response(data_file, raw_response)
        data = self.translate(raw_response, 'Technical Analysis: MACD')
        return data

    def get_sma_response(self):
        indicator_key = self.get_indicator_key()  # e.g. BTCUSD
        query = {
            "function": "SMA",
            "symbol": indicator_key,
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
            "function": "RSI",
            "symbol": indicator_key,
            "interval": self.rsi_interval.value,
            "time_period": int(self.rsi_period),
            "series_type": self.rsi_series_type.value,
        }
        raw_response, data_file = self.get_url_response(self.url, query)
        self.validate_json_response(data_file, raw_response)
        key = 'Technical Analysis: RSI'
        data = self.translate(raw_response, key)
        return data

    def get_earnings_response(self):
        if self.earnings_interval.timedelta <= TimeInterval.QUARTER.timedelta:
            period = 'quarter'
        elif self.earnings_interval.timedelta <= TimeInterval.YEAR.timedelta:
            period = 'annual'
        else:
            raise RuntimeError(
                'Interval is not supported: {} (for: {})'.format(self.earnings_interval, self.__class__.__name__))
        last = self.span / self.earnings_interval.timedelta
        query = {'period': period, 'last': last}
        raw_response, data_file = self.get_url_response('{}/stock/{}/earnings'.format(self.url,
                                                                                      self.symbol),
                                                        query)
        key = 'earnings'
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
        if self.income_interval.timedelta <= TimeInterval.QUARTER.timedelta:
            period = 'quarter'
        elif self.income_interval.timedelta <= TimeInterval.YEAR.timedelta:
            period = 'annual'
        else:
            raise RuntimeError(
                'Interval is not supported: {} (for: {})'.format(self.income_interval, self.__class__.__name__))
        last = self.span / self.income_interval.timedelta
        query = {'period': period, 'last': last}
        raw_response, data_file = self.get_url_response('{}/stock/{}/income'.format(self.url,
                                                                                    self.symbol),
                                                        query)
        key = 'income'
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
            dt = datetime.strptime(entry['fiscalDate'], data_date_format)
            translated[dt] = {}
            for seriesType in ValueType:
                value = self.get_value_or_none(entry, seriesType)
                if value is not None:
                    ratio = self.get_adjusted_ratio(entry)
                    value = value * ratio
                    translated[dt][seriesType] = value
        return translated

    def get_balance_sheet_response(self):
        if self.balance_sheet_interval.timedelta <= TimeInterval.QUARTER.timedelta:
            if self.self.calculation_type == 'FINANCIALS':
                period = '10-Q'
            else:
                period = 'quarter'
        elif self.balance_sheet_interval.timedelta <= TimeInterval.YEAR.timedelta:
            if self.calculation_type == 'FINANCIALS':
                period = '10-K'
            else:
                period = 'annual'
        else:
            raise RuntimeError('Interval is not supported: {} (for: {})'.format(self.balance_sheet_interval, self.__class__.__name__))
        last = int(self.span / self.balance_sheet_interval.timedelta)
        if self.calculation_type == 'FINANCIALS':
            query = {'last': last}
            raw_response, data_file = self.get_url_response('{}/time-series/REPORTED_FINANCIALS/{}/{}'.format(self.url, self.symbol, period), query)
            data = self.translate_financials(raw_response)
        else:
            query = {'period': period, 'last': last}
            raw_response, data_file = self.get_url_response('{}/stock/{}/balance-sheet'.format(self.url, self.symbol), query)
            key = 'balancesheet'
            data = self.translate_balance_sheet(raw_response, key)
        return data

    def translate_financials(self, response_data, data_date_format='%Y-%m-%d'):
        translated = {}
        for entry in response_data:
            dt = datetime.fromtimestamp(entry['date'] / 1000)
            translated[dt] = {}
            for seriesType in ValueType:
                value = self.get_value_or_none(entry, seriesType)
                if value is not None:
                    ratio = self.get_adjusted_ratio(entry)
                    value = value * ratio
                    translated[dt][seriesType] = value
        return translated

    def translate_balance_sheet(self, response_data, key, data_date_format='%Y-%m-%d'):
        if key not in response_data:
            raise RuntimeError("Failed to find key in data: {}".format(key))
        if not response_data[key]:
            raise RuntimeError(
                "There is no data (length is 0) for key: {} (maybe try a different time interval)".format(key))
        translated = {}
        for entry in response_data[key]:
            dt = datetime.strptime(entry['fiscalDate'], data_date_format)
            translated[dt] = {}
            for seriesType in ValueType:
                value = self.get_value_or_none(entry, seriesType)
                if value is not None:
                    ratio = self.get_adjusted_ratio(entry)
                    value = value * ratio
                    translated[dt][seriesType] = value
        return translated

    def get_cash_flow_response(self):
        if self.cash_flow_interval.timedelta <= TimeInterval.QUARTER.timedelta:
            period = 'quarter'
        elif self.cash_flow_interval.timedelta <= TimeInterval.YEAR.timedelta:
            period = 'annual'
        else:
            raise RuntimeError(
                'Interval is not supported: {} (for: {})'.format(self.cash_flow_interval, self.__class__.__name__))
        last = self.span / self.cash_flow_interval.timedelta
        query = {'period': period, 'last': last}
        raw_response, data_file = self.get_url_response('{}/stock/{}/cash-flow'.format(self.url,
                                                                                       self.symbol),
                                                        query)
        key = 'cashflow'
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
            dt = datetime.strptime(entry['fiscalDate'], data_date_format)
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
        """
        Currently the SEC adapter does not provide currency data, so...
        :return: False
        """
        return False
        # query = {}
        # data, data_file = self.get_url_response('{}/ref-data/crypto/symbols'.format(self.url), query)
        # data = [item['symbol'] for item in data]
        # return '{}{}'.format(self.symbol, self.base_symbol) in data

    def get_is_listed(self) -> bool:
        data = self.get_equities_list()
        return self.symbol in data

    def get_is_physical_currency(self):
        """
        Currently the SEC adapter does not provide currency data, so...
        :return: True
        """
        return True
        # query = {}
        # data, data_file = self.get_url_response('{}/ref-data/fx/symbols'.format(self.url), query)
        # data = [item['code'] for item in data['currencies']]
        # return self.base_symbol in data
