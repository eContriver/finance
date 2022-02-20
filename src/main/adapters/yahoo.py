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

#
#
#
import os.path
from datetime import datetime, timedelta
from typing import Dict, Optional

import robin_stocks as rs

import pandas
import pandas_datareader
from pandas_datareader import DataReader

from main.application.adapter import AssetType, DataType, Adapter
from main.application.time_interval import TimeInterval
from main.application.value_type import ValueType
from main.common.time_zones import TimeZones


class Yahoo(Adapter):
    span: timedelta
    name: str = 'yahoo'

    def __init__(self, symbol: str, asset_type: Optional[AssetType] = None):
        super().__init__(symbol, asset_type)
        script_dir = os.path.dirname(os.path.realpath(__file__))
        self.cache_dir = os.path.join(script_dir, '..', '..', '..', '.cache', Yahoo.name)
        # self.span = '5year'
        # 'hour', 'day', 'week', 'month', '3month', 'year', '5year'
        years = 10
        self.span = timedelta(weeks=52*years)

    @staticmethod
    def find_symbol_in_data(data, entry):
        contains = False
        for row in data:
            if row[0] == entry:
                contains = True
                break
        return contains

    def delay_requests(self, data_file: str) -> None:
        pass

    def get_is_listed(self) -> bool:
        today: datetime = datetime.now(TimeZones.get_tz())
        # yesterday = today - timedelta(days=1)
        args = {
            'name': self.symbol,
            'data_source': Yahoo.name,
            'start': today.strftime('%Y-%m-%d'),
            'end': today.strftime('%Y-%m-%d')
        }
        found_listed = False
        try:
            raw_response, data_file = self.get_api_response(DataReader, args, cache=True, data_type=DataType.DATA_FRAME)
            found_listed = raw_response.shape[0] >= 1
        except (pandas_datareader._utils.RemoteDataError):
            pass  # this means that the symbol was not found
        return found_listed

    def get_is_digital_currency(self) -> bool:
        return False

    def get_is_physical_currency(self) -> bool:
        return 'USD' == self.base_symbol

    def get_stock_series_response(self):
        today: datetime = datetime.now(TimeZones.get_tz())
        today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        # yesterday = today - timedelta(days=1)
        args = {
            'name': self.symbol,
            'data_source': Yahoo.name,
            'start': today - self.span,
            'end': today
        }
        raw_response, data_file = self.get_api_response(DataReader, args, cache=True, data_type=DataType.DATA_FRAME)
        data = self.translate_series(raw_response)
        return data

    def translate_interval(self):
        if self.series_interval == TimeInterval.DAY:
            interval = 'day'
        else:
            raise RuntimeError('Unknown interval: {}'.format(self.series_interval))
        return interval

    def translate_series(self, response_data, data_date_format='%Y-%m-%dT%H:%M:%SZ') -> Dict[datetime, Dict[ValueType, float]]:
        translated = {}
        assert not response_data.empty, "The response data was empty"
        to_translate = response_data.copy()
        to_translate.index = pandas.to_datetime(to_translate.index)
        # translated = translated.apply(self.)
        to_translate = response_data.to_dict(orient='index')
        for instance, values in to_translate.items():
            translated[instance] = {}
            for value_type in ValueType:
                value = get_response_value_or_none(values, value_type)
                if value is not None:
                    ratio = self.get_adjusted_ratio(values)
                    value = value * ratio
                    translated[instance][value_type] = value
        return translated

    def get_digital_series_response(self):
        args = {
            "symbol": self.symbol,
            "span": self.span,  # self.end_at...
            "interval": self.translate_interval(),
        }
        raw_response, data_file = self.get_api_response(rs.yahoo.get_crypto_historicals, args)
        assert raw_response, "The response data was empty"
        data = self.translate_series(raw_response)
        return data

    def get_indicator_key(self):
        self.calculate_asset_type()
        indicator_key = self.symbol
        if self.asset_type == AssetType.DIGITAL_CURRENCY:
            indicator_key = "{}-{}".format(self.symbol, self.base_symbol)  # e.g. BTC-USD
        return indicator_key

    def get_holdings(self):
        data = self.get_stock_positions()
        data = merge(data, self.get_crypto_positions())
        data = merge(data, self.get_account_info())
        return data

    def get_historic_value(self) -> Dict[datetime, float]:
        args = {
            'span': 'month',
            'interval': 'day',
            # 'bounds': 'extended',
        }
        raw_response, data_file = self.get_api_response(rs.yahoo.get_historical_portfolio, args, cache=False)
        assert raw_response, "The response data was empty"
        if len(raw_response) == 1:
            assert raw_response[0] is not None, "The response data was empty"
        data: Dict[datetime, float] = self.translate_portfolio(raw_response['equity_historicals'])
        return data

    @staticmethod
    def translate_portfolio(response_data, data_date_format='%Y-%m-%dT%H:%M:%SZ') -> Dict[datetime, float]:
        translated: Dict[datetime, float] = {}
        assert response_data, "The response data was empty"
        for item in response_data:
            assert item is not None, "Received a None item while translating response data"
            dt = datetime.strptime(item['begins_at'], data_date_format)
            translated[dt] = float(item['adjusted_close_equity'])
        return translated

    def get_account_info(self):
        args = {
        }
        raw_response, data_file = self.get_api_response(rs.yahoo.load_phoenix_account, args, cache=False)
        assert raw_response, "The response data was empty"
        data = {
            raw_response['account_buying_power']['currency_code']: float(raw_response['account_buying_power']['amount'])
        }
        return data

    # def get_stock_positions(self):
    #     args = {
    #     }
    #     raw_response, data_file = self.get_api_response(rs.yahoo.build_holdings, args, cache=False)
    #     assert raw_response, "The response data was empty"
    #     data = {}
    #     for symbol, item in raw_response.items():
    #         data[symbol] = float(item['quantity'])
    #     return data

    def get_crypto_positions(self):
        args = {
        }
        raw_response, data_file = self.get_api_response(rs.yahoo.get_crypto_positions, args, cache=False)
        assert raw_response, "The response data was empty"
        data = {}
        for item in raw_response:
            data[item['currency']['code']] = float(item['quantity'])
        return data

    def get_open_orders(self):
        orders = self.get_open_stock_orders()
        orders += self.get_open_crypto_orders()
        return orders

    # def get_open_stock_orders(self):
    #     args = {
    #     }
    #     raw_response, data_file = self.get_api_response(rs.yahoo.get_all_open_stock_orders, args, cache=False)
    #     orders = []
    #     for item in raw_response:
    #         side = OrderSide.BUY if item['side'] == 'buy' else OrderSide.SELL
    #         data_date_format = '%Y-%m-%dT%H:%M:%S.%f%z'
    #         dt = datetime.strptime(item['created_at'], data_date_format)
    #
    #         args = {
    #             'url': item['instrument']
    #         }
    #         instrument_response, instrument_file = self.get_api_response(rs.yahoo.get_instrument_by_url, args)
    #
    #         if item['type'] == 'limit':
    #             orders.append(LimitOrder(instrument_response['symbol'], side, float(item['price']), float(item['quantity']), dt))
    #         elif item['type'] == 'stop':
    #             orders.append(StopOrder(instrument_response['symbol'], side, float(item['price']), float(item['quantity']), dt))
    #         else:
    #             raise RuntimeError("Unsupported order type: {}".format(item['type']))
    #     return orders
    #     # orders = self.translate_orders(raw_response, rs.yahoo.get_stock_order_info)
    #     # return orders

    # def get_open_crypto_orders(self):
    #     args = {
    #     }
    #     raw_response, data_file = self.get_api_response(rs.yahoo.get_all_open_crypto_orders, args, cache=False)
    #     orders = []
    #     for item in raw_response:
    #         side = OrderSide.BUY if item['side'] == 'buy' else OrderSide.SELL
    #         data_date_format = '%Y-%m-%dT%H:%M:%S.%f%z'
    #         dt = datetime.strptime(item['created_at'], data_date_format)
    #
    #         args = {
    #         }
    #         pair_response, pair_file = self.get_api_response(rs.yahoo.get_currency_pairs, args)
    #
    #         symbol = None
    #         for pair_item in pair_response:
    #             if pair_item['id'] == item['currency_pair_id']:
    #                 symbol = pair_item['asset_currency']['code']
    #
    #         if item['type'] == 'limit':
    #             orders.append(LimitOrder(symbol, side, float(item['price']), float(item['quantity']), dt))
    #         elif item['type'] == 'stop':
    #             orders.append(StopOrder(symbol, side, float(item['price']), float(item['quantity']), dt))
    #         else:
    #             raise RuntimeError("Unsupported order type: {}".format(item['type']))
    #     return orders
    #     # orders = self.translate_orders(raw_response, rs.yahoo.get_crypto_order_info)
    #     # return orders

    # def translate_orders(self, raw_response, info_api):
    #     orders = []
    #     for item in raw_response:
    #         side = OrderSide.BUY if item['side'] == 'buy' else OrderSide.SELL
    #         data_date_format = '%Y-%m-%dT%H:%M:%S.%f%z'
    #         dt = datetime.strptime(item['created_at'], data_date_format)
    #         order_id = item['id']
    #         order_info = self.get_order_info(info_api, order_id)
    #         if item['type'] == 'limit':
    #             orders.append(LimitOrder(order_info['symbol'], side, float(item['price']), float(item['quantity']), dt))
    #         elif item['type'] == 'stop':
    #             orders.append(LimitOrder(order_info['symbol'], side, float(item['price']), float(item['quantity']), dt))
    #         else:
    #             raise RuntimeError("Unsupported order type: {}".format(item['type']))
    #     return orders
    #
    # def get_order_info(self, info_api, order_id):
    #     if info_api == rs.yahoo.get_stock_order_info:
    #         args = {'orderID': order_id}
    #     else:
    #         args = {'order_id': order_id}
    #     raw_response, data_file = self.get_api_response(info_api, args, cache=False)
    #     return raw_response
