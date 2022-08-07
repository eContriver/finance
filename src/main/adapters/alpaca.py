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

from datetime import datetime, timedelta
from os import environ
from typing import List, Optional, Union

import pandas
from alpaca.common import RawData
from alpaca.data import StockBarsRequest, StockHistoricalDataClient, TimeFrame, BarSet

from main.application.adapter import DataType, AssetType, Adapter, insert_column
from main.application.argument import ArgumentKey
from main.application.converter import Converter
from main.application.time_interval import TimeInterval
from main.application.value_type import ValueType
from main.common.locations import file_link_format


class Alpaca(Adapter):
    name: str = 'alpaca'
    url: str = 'https://paper-api.alpaca.markets'

    def __init__(self, symbol: str, asset_type: Optional[AssetType] = None):
        api_key = self.get_and_check_env_var('https://alpaca.markets', 'ALPACA_API_KEY')
        api_secret = self.get_and_check_env_var('https://alpaca.markets', 'ALPACA_API_SECRET')
        self.client = StockHistoricalDataClient(api_key, api_secret)
        super().__init__(symbol, asset_type)
        self.converters: List[Converter] = [
            # we allow for multiple strings to be converted into the value type, first match is used
            Converter(ValueType.OPEN, self.get_prices_response, ['open'], adjust_values=True),
            Converter(ValueType.HIGH, self.get_prices_response, ['high'], adjust_values=True),
            Converter(ValueType.LOW, self.get_prices_response, ['low'], adjust_values=True),
            Converter(ValueType.CLOSE, self.get_prices_response, ['close'], adjust_values=True),
            Converter(ValueType.VOLUME, self.get_prices_response, ['volume']),
            # Converter(ValueType.RSI, self.get_rsi_response, ['RSI']),
            # Converter(ValueType.MACD, self.get_macd_response, ['MACD']),
            # Converter(ValueType.MACD_HIST, self.get_macd_response, ['MACD_Hist']),
            # Converter(ValueType.MACD_SIGNAL, self.get_macd_response, ['MACD_Signal']),
            # Converter(ValueType.SMA, self.get_sma_response, ['SMA']),
            # Converter(ValueType.EPS, self.get_earnings_response, ['reportedEPS']),
            # Converter(ValueType.REVENUE, self.get_income_response, ['totalRevenue']),
        ]

    @staticmethod
    def get_and_check_env_var(docs_url, key):
        if environ.get(key) is None:
            raise RuntimeError(
                f"The {key} environment variable is not set - this needs to be set to the API KEY for "
                f"your account from the {docs_url} site.")
        api_key = environ.get(key)
        return api_key

    def get_equities_list(self) -> List[str]:
        query = {
            "apikey": self.api_key,
            "function": "LISTING_STATUS",
        }
        data, data_file = self.get_url_response(self.url, query, cache=True, data_type=DataType.CSV)
        data = data[1:]  # remove header
        data = [item[0] for item in data]
        return data

    def get_prices_response(self, value_type: ValueType) -> None:
        # if self.asset_type is AssetType.DIGITAL_CURRENCY:
        #     self.get_digital_currency_response(value_type)
        # else:
        self.get_stock_prices_response(value_type)

    def get_stock_prices_response(self, value_type: ValueType) -> None:
        end_time: Optional[datetime] = self.get_argument_value(ArgumentKey.END_TIME)
        end_time = datetime.now() if end_time is None else end_time
        start_time: Optional[datetime] = self.get_argument_value(ArgumentKey.START_TIME)
        start_time = end_time - timedelta(days=1) if start_time is None else start_time
        interval: TimeInterval = self.get_argument_value(ArgumentKey.INTERVAL)
        timeframe: TimeFrame = TimeFrame.Hour
        if interval == TimeInterval.HOUR:
            timeframe = TimeFrame.Hour
        elif interval == TimeInterval.MIN1:
            timeframe = TimeFrame.Minute
        elif interval == TimeInterval.WEEK:
            timeframe = TimeFrame.Week
        query = {
            "symbol_or_symbols": [self.symbol],
            "timeframe": timeframe,
            "start": start_time,
            "end": end_time
        }

        def capture(this):
            def get_stock_bars(**callback_args) -> pandas.DataFrame:
                request_params = StockBarsRequest(**callback_args)
                response: Union[BarSet, RawData] = this.client.get_stock_bars(request_params)
                return response.df
            return get_stock_bars
        raw_response, data_file = self.get_api_response(capture(self), query, cache=True, data_type=DataType.DATA_FRAME)
        self.validate_response(data_file, raw_response)
        self.translate_series(raw_response, value_type, self.symbol)


    def translate_series(self, response_data, value_type: ValueType, key: str, data_date_format='%Y-%m-%d') -> None:
        """
        This method converts the raw data returned from rest API calls into
        :param response_data: Data from an API or URL request (raw data generally JSON, CSV, etc.)
        :param value_type: The value type we will be converting and the column we will be inserting
        :param key: The root key where we will pull the dictionary out of
        :param data_date_format: The incoming data time format, used to convert to datetime objects
        :return: None
        """

        to_translate = response_data.copy()
        to_translate = to_translate.reset_index(level=0, drop=True) # SYMBOL/DATE multiindex to DATE index
        if to_translate.empty:
            raise RuntimeError(
                "There is no data (length is 0) for key: '{}' (maybe try a different time interval)".format(key))
        for converter in self.converters:
            if converter.value_type in self.data:
                continue  # if we've already added this value type, then don't do it again
            if converter.value_type != value_type:
                continue
            indexes = []
            values = []
            for response_key, response_entry in to_translate.items():
                value = None
                for entry_datetime, response_value in response_entry.items():
                    if response_key in converter.response_keys:
                        value = float(response_value)
                    if value is None:  # we didn't find a match so move on to the next thing to convert
                        continue
                    # if converter.adjust_values:
                        # ratio = get_adjusted_ratio(response_entry)
                        # value = value * ratio
                    indexes.append(entry_datetime.to_datetime64())
                    values.append(value)
            insert_column(self.data, converter.value_type, indexes, values)


    @staticmethod
    def validate_response(data_file, raw_response, expects_meta_data=True):
        if raw_response.empty:
            raise RuntimeError("The response data is empty, binary data file: {}"
                               .format(file_link_format(data_file)))

    def get_indicator_key(self):
        self.calculate_asset_type()
        indicator_key = self.symbol
        if self.asset_type == AssetType.DIGITAL_CURRENCY:
            indicator_key = self.symbol + self.base_symbol  # e.g. BTCUSD
        return indicator_key

    def delay_requests(self, data_file: str) -> None:
        # request_limit_with_timedelta_delay(buffer=10, historic_requests=self.get_create_times(),
        #                                    max_timeframe=timedelta(minutes=1), max_requests=5)
        pass

    def get_is_digital_currency(self):
        return False
        # data, data_file = self.get_url_response("https://www.alphavantage.co/digital_currency_list", {},
        #                                         cache=True, data_type=DataType.CSV, delay=False)
        # data = data[1:]  # remove header
        # data = [item[0] for item in data]
        # return self.symbol in data

    def get_is_listed(self) -> bool:
        # TODO: if we want to support crypto, then either find a way to dta drive the stocks available
        # or just manually override with asset_type_override: ETH: DIGITAL_CURRENCY
        return True
        # data = self.get_equities_list()
        # return self.symbol in data

    def get_is_physical_currency(self):
        data, data_file = self.get_url_response("https://www.alphavantage.co/physical_currency_list", {},
                                                cache=True, data_type=DataType.CSV, delay=False)
        data = data[1:]  # remove header
        data = [item[0] for item in data]
        return self.base_symbol in data
