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


# import os.path
# from datetime import datetime, timedelta
# from os import environ
# from typing import Optional, Dict
#
# import quandl
#
# from main.adapters.adapter import TimeInterval, AssetType, QueryType, DataType
# from main.adapters.valueType import ValueType
# from main.adapters.calculators.series import Series
# from main.portfolio.order import LimitOrder, OrderSide, StopOrder
#
#
# class Quandl(Series):
#     span: str
#
#     def __init__(self, symbol: str, base_symbol: str = 'USD',
#                  cache_key_date: Optional[datetime] = None, span: Optional[timedelta] = None):
#         if environ.get('QUANDL_API_KEY') is None:
#             raise RuntimeError(
#                 "The QUANDL_API_KEY environment variable is not set - this needs to be set to the API KEY for "
#                 "your account from the quandl.com site.")
#         quandl.ApiConfig.api_key = environ.get('QUANDL_API_KEY')
#         super().__init__(symbol, base_symbol, cache_key_date, span)
#         script_dir = os.path.dirname(os.path.realpath(__file__))
#         self.cache_dir = os.path.join(script_dir, '..', '..', '..', '..', '.cache', 'quandl')
#         # self.span = '5year'
#         # 'hour', 'day', 'week', 'month', '3month', 'year', '5year'
#         self.span = 'year'
#
#     @staticmethod
#     def find_symbol_in_data(data, entry):
#         contains = False
#         for row in data:
#             if row[0] == entry:
#                 contains = True
#                 break
#         return contains
#
#     def get_is_listed(self) -> bool:
#         url = 'https://static.quandl.com/nasdaqomx/indexes.csv'
#         data, data_file = self.get_url_response(url, {}, cache=True, data_type=DataType.CSV)
#         return 'trading_halted' in data and not data['trading_halted']
#
#     def get_is_digital_currency(self) -> bool:
#         # :param dataset: str or list, depending on single dataset usage or multiset usage
#         #         Dataset codes are available on the Quandl website
#         # :param str api_key: Downloads are limited to 50 unless api_key is specified
#         # :param str start_date, end_date: Optional datefilers, otherwise entire
#         #        dataset is returned
#         # :param str collapse: Options are daily, weekly, monthly, quarterly, annual
#         # :param str transform: options are diff, rdiff, cumul, and normalize
#         # :param int rows: Number of rows which will be returned
#         # :param str order: options are asc, desc. Default: `asc`
#         # :param str returns: specify what format you wish your dataset returned as,
#         #     either `numpy` for a numpy ndarray or `pandas`. Default: `pandas`
#         # :returns: :class:`pandas.DataFrame` or :class:`numpy.ndarray`
#         data_type = DataType.DATAFRAME
#         args = {
#             'dataset': 'BITFINEX/{}{}'.format(self.symbol, self.base_symbol),
#             'returns': 'pandas' if data_type is DataType.DATAFRAME else 'numpy',
#         }
#         data, data_file = self.get_api_response(quandl.get, args, cache=True, data_type=data_type)
#         is_digital = False
#         for item in data:
#             if 'asset_currency' in item and item['asset_currency']['code'] == self.symbol:
#                 is_digital = True
#                 break
#         return is_digital
#
#     def get_is_physical_currency(self) -> bool:
#         data, data_file = self.get_api_response(quandl.get_currency_pairs, {})
#         is_physical = False
#         for item in data:
#             if 'quote_currency' in item and item['quote_currency']['code'] == self.base_symbol:
#                 is_physical = True
#                 break
#         return is_physical
#
#     def place_buy_limit_order(self, quantity: float, price: float):
#         args = {
#             "symbol": self.symbol,
#             "quantity": quantity,
#             "limitPrice": price,
#         }
#         if self.asset_type == AssetType.DIGITAL_CURRENCY:
#             raw_response, data_file = self.get_api_response(quandl.order_buy_crypto_limit, args)
#         elif self.asset_type == AssetType.EQUITY:
#             raw_response, data_file = self.get_api_response(quandl.order_buy_limit, args)
#         else:
#             raise RuntimeError("Adapter is set with unsupported asset type:{}".format(self.asset_type))
#         data = self.translate_order(raw_response)
#         return data
#
#     def place_sell_limit_order(self, quantity: float, price: float):
#         args = {
#             "symbol": self.symbol,
#             "quantity": quantity,
#             "limitPrice": price,
#         }
#         if self.asset_type == AssetType.DIGITAL_CURRENCY:
#             raw_response, data_file = self.get_api_response(quandl.order_sell_crypto_limit, args)
#         elif self.asset_type == AssetType.EQUITY:
#             raw_response, data_file = self.get_api_response(quandl.order_sell_limit, args)
#         else:
#             raise RuntimeError("Adapter is set with unsupported asset type:{}".format(self.asset_type))
#         data = self.translate_order(raw_response)
#         return data
#
#     def place_buy_market_order(self, quantity: float):
#         args = {
#             "symbol": self.symbol,
#             "quantity": quantity,
#         }
#         if self.asset_type == AssetType.DIGITAL_CURRENCY:
#             raw_response, data_file = self.get_api_response(quandl.order_buy_crypto_by_quantity, args)
#         elif self.asset_type == AssetType.EQUITY:
#             raw_response, data_file = self.get_api_response(quandl.order_buy_market, args)
#         else:
#             raise RuntimeError("Adapter is set with unsupported asset type:{}".format(self.asset_type))
#         data = self.translate_order(raw_response)
#         return data
#
#     def place_sell_market_order(self, quantity: float):
#         args = {
#             "symbol": self.symbol,
#             "quantity": quantity,
#         }
#         if self.asset_type == AssetType.DIGITAL_CURRENCY:
#             raw_response, data_file = self.get_api_response(quandl.order_sell_crypto_by_quantity, args)
#         elif self.asset_type == AssetType.EQUITY:
#             raw_response, data_file = self.get_api_response(quandl.order_sell_market, args)
#         else:
#             raise RuntimeError("Adapter is set with unsupported asset type:{}".format(self.asset_type))
#         data = self.translate_order(raw_response)
#         return data
#
#     def place_buy_stop_order(self, quantity: float, price: float):
#         args = {
#             "symbol": self.symbol,
#             "quantity": quantity,
#             "stopPrice": price,
#         }
#         if self.asset_type == AssetType.EQUITY:
#             raw_response, data_file = self.get_api_response(quandl.order_buy_stop_loss, args)
#         else:
#             raise RuntimeError("Adapter is set with unsupported asset type:{}".format(self.asset_type))
#         data = self.translate_order(raw_response)
#         return data
#
#     def place_sell_stop_order(self, quantity: float, price: float):
#         args = {
#             "symbol": self.symbol,
#             "quantity": quantity,
#             "stopPrice": price,
#         }
#         raw_response, data_file = self.get_api_response(quandl.order_sell_crypto_by_price, args)
#         # if self.asset_type == AssetType.EQUITY:
#         #     raw_response, data_file = self.get_api_response(quandl.order_sell_stop_loss, args)
#         # else:
#         #     raise RuntimeError("Adapter is set with unsupported asset type:{}".format(self.asset_type))
#         data = self.translate_order(raw_response)
#         return data
#
#     @staticmethod
#     def translate_order(response_data, data_date_format='%Y-%m-%dT%H:%M:%S.%f%z'):
#         translated = {}
#         assert response_data is not None, "Received a None item while translating response data"
#         dt = datetime.strptime(response_data['created_at'], data_date_format)
#         translated[dt] = {}
#         translated[dt][QueryType.ORDERING] = {}
#         translated[dt][QueryType.ORDERING]['price'] = response_data['price']
#         translated[dt][QueryType.ORDERING]['quantity'] = response_data['quantity']
#         return translated
#
#     def get_stock_series_response(self):
#         args = {
#             "inputSymbols": self.symbol,
#             "span": self.span,  # self.end_at...
#             "interval": self.translate_interval(),
#         }
#         raw_response, data_file = self.get_api_response(quandl.get_stock_historicals, args)
#         data = self.translate(raw_response)
#         return data
#
#     def translate_interval(self):
#         if self.series_interval == TimeInterval.MIN5:
#             interval = '5minute'
#         elif self.series_interval == TimeInterval.MIN10:
#             interval = '10minute'
#         elif self.series_interval == TimeInterval.HOUR:
#             interval = 'hour'
#         elif self.series_interval == TimeInterval.DAY:
#             interval = 'day'
#         elif self.series_interval == TimeInterval.WEEK:
#             interval = 'week'
#         else:
#             raise RuntimeError('Unknown interval: {}'.format(self.series_interval))
#         return interval
#
#     def translate(self, response_data, data_date_format='%Y-%m-%dT%H:%M:%SZ') -> Dict[datetime, Dict[ValueType, float]]:
#         translated = {}
#         assert response_data, "The response data was empty"
#         for item in response_data:
#             assert item is not None, "Received a None item while translating response data"
#             dt = datetime.strptime(item['begins_at'], data_date_format)
#             translated[dt] = {}
#             for value_type in ValueType:
#                 value = self.get_value_or_none(item, value_type)
#                 if value is not None:
#                     ratio = self.get_adjusted_ratio(item)
#                     value = value * ratio
#                     translated[dt][value_type] = value
#         return translated
#
#     def get_digital_series_response(self):
#         args = {
#             "symbol": self.symbol,
#             "span": self.span,  # self.end_at...
#             "interval": self.translate_interval(),
#         }
#         raw_response, data_file = self.get_api_response(quandl.get_crypto_historicals, args)
#         assert raw_response, "The response data was empty"
#         data = self.translate(raw_response)
#         return data
#
#     def get_indicator_key(self):
#         self.calculate_asset_type()
#         indicator_key = self.symbol
#         if self.asset_type == AssetType.DIGITAL_CURRENCY:
#             indicator_key = "{}-{}".format(self.symbol, self.base_symbol)  # e.g. BTC-USD
#         return indicator_key
#
#     def get_holdings(self):
#         data = self.get_stock_positions()
#         data = self.merge(data, self.get_crypto_positions())
#         data = self.merge(data, self.get_account_info())
#         return data
#
#     def get_historic_value(self, series_adapter: Series = None) -> Dict[datetime, float]:
#         args = {
#             'span': 'month',
#             'interval': 'day',
#             # 'bounds': 'extended',
#         }
#         raw_response, data_file = self.get_api_response(quandl.get_historical_portfolio, args, cache=False)
#         assert raw_response, "The response data was empty"
#         if len(raw_response) == 1:
#             assert raw_response[0] is not None, "The response data was empty"
#         data: Dict[datetime, float] = self.translate_portfolio(raw_response['equity_historicals'])
#         return data
#
#     @staticmethod
#     def translate_portfolio(response_data, data_date_format='%Y-%m-%dT%H:%M:%SZ') -> Dict[datetime, float]:
#         translated: Dict[datetime, float] = {}
#         assert response_data, "The response data was empty"
#         for item in response_data:
#             assert item is not None, "Received a None item while translating response data"
#             dt = datetime.strptime(item['begins_at'], data_date_format)
#             translated[dt] = float(item['adjusted_close_equity'])
#         return translated
#
#     def get_account_info(self):
#         args = {
#         }
#         raw_response, data_file = self.get_api_response(quandl.load_phoenix_account, args, cache=False)
#         assert raw_response, "The response data was empty"
#         data = {
#             raw_response['account_buying_power']['currency_code']: float(raw_response['account_buying_power']['amount'])
#         }
#         return data
#
#     def get_stock_positions(self):
#         args = {
#         }
#         raw_response, data_file = self.get_api_response(quandl.build_holdings, args, cache=False)
#         assert raw_response, "The response data was empty"
#         data = {}
#         for symbol, item in raw_response.items():
#             data[symbol] = float(item['quantity'])
#         return data
#
#     def get_crypto_positions(self):
#         args = {
#         }
#         raw_response, data_file = self.get_api_response(quandl.get_crypto_positions, args, cache=False)
#         assert raw_response, "The response data was empty"
#         data = {}
#         for item in raw_response:
#             data[item['currency']['code']] = float(item['quantity'])
#         return data
#
#     def get_open_orders(self):
#         orders = self.get_open_stock_orders()
#         orders += self.get_open_crypto_orders()
#         return orders
#
#     def get_open_stock_orders(self):
#         args = {
#         }
#         raw_response, data_file = self.get_api_response(quandl.get_all_open_stock_orders, args, cache=False)
#         orders = []
#         for item in raw_response:
#             side = OrderSide.BUY if item['side'] == 'buy' else OrderSide.SELL
#             data_date_format = '%Y-%m-%dT%H:%M:%S.%f%z'
#             dt = datetime.strptime(item['created_at'], data_date_format)
#
#             args = {
#                 'url': item['instrument']
#             }
#             instrument_response, instrument_file = self.get_api_response(quandl.get_instrument_by_url, args)
#
#             if item['type'] == 'limit':
#                 orders.append(LimitOrder(instrument_response['symbol'], side, float(item['price']), float(item['quantity']), dt))
#             elif item['type'] == 'stop':
#                 orders.append(StopOrder(instrument_response['symbol'], side, float(item['price']), float(item['quantity']), dt))
#             else:
#                 raise RuntimeError("Unsupported order type: {}".format(item['type']))
#         return orders
#         # orders = self.translate_orders(raw_response, quandl.get_stock_order_info)
#         # return orders
#
#     def get_open_crypto_orders(self):
#         args = {
#         }
#         raw_response, data_file = self.get_api_response(quandl.get_all_open_crypto_orders, args, cache=False)
#         orders = []
#         for item in raw_response:
#             side = OrderSide.BUY if item['side'] == 'buy' else OrderSide.SELL
#             data_date_format = '%Y-%m-%dT%H:%M:%S.%f%z'
#             dt = datetime.strptime(item['created_at'], data_date_format)
#
#             args = {
#             }
#             pair_response, pair_file = self.get_api_response(quandl.get_currency_pairs, args)
#
#             symbol = None
#             for pair_item in pair_response:
#                 if pair_item['id'] == item['currency_pair_id']:
#                     symbol = pair_item['asset_currency']['code']
#
#             if item['type'] == 'limit':
#                 orders.append(LimitOrder(symbol, side, float(item['price']), float(item['quantity']), dt))
#             elif item['type'] == 'stop':
#                 orders.append(StopOrder(symbol, side, float(item['price']), float(item['quantity']), dt))
#             else:
#                 raise RuntimeError("Unsupported order type: {}".format(item['type']))
#         return orders
#         # orders = self.translate_orders(raw_response, quandl.get_crypto_order_info)
#         # return orders
#
#     # def translate_orders(self, raw_response, info_api):
#     #     orders = []
#     #     for item in raw_response:
#     #         side = OrderSide.BUY if item['side'] == 'buy' else OrderSide.SELL
#     #         data_date_format = '%Y-%m-%dT%H:%M:%S.%f%z'
#     #         dt = datetime.strptime(item['created_at'], data_date_format)
#     #         order_id = item['id']
#     #         order_info = self.get_order_info(info_api, order_id)
#     #         if item['type'] == 'limit':
#     #             orders.append(LimitOrder(order_info['symbol'], side, float(item['price']), float(item['quantity']), dt))
#     #         elif item['type'] == 'stop':
#     #             orders.append(LimitOrder(order_info['symbol'], side, float(item['price']), float(item['quantity']), dt))
#     #         else:
#     #             raise RuntimeError("Unsupported order type: {}".format(item['type']))
#     #     return orders
#     #
#     # def get_order_info(self, info_api, order_id):
#     #     if info_api == quandl.get_stock_order_info:
#     #         args = {'orderID': order_id}
#     #     else:
#     #         args = {'order_id': order_id}
#     #     raw_response, data_file = self.get_api_response(info_api, args, cache=False)
#     #     return raw_response
