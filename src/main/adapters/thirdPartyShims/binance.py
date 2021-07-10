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


#import logging
#import os.path
#import time
#from datetime import datetime, timedelta
#from os import environ
#from typing import Optional, Dict
#
#from binance.client import Client
#
#from main.adapters.adapter import TimeInterval, AssetType, QueryType
#from main.adapters.valueType import ValueType
#from main.adapters.indicators.series import Series
#from main.adapters.orders.order import Order
#from main.portfolio.order import LimitOrder, OrderSide, StopOrder
#
#
## Override if needed to deal with timestamp issue
#class CustomClient(Client):
#    TIME_DELTA = None
#
#    def _request(self, method, uri, signed, force_params=False, **kwargs):
#
#        # set default requests timeout
#        kwargs['timeout'] = 10
#
#        # add our global requests params
#        if self._requests_params:
#            kwargs.update(self._requests_params)
#
#        data = kwargs.get('data', None)
#        if data and isinstance(data, dict):
#            kwargs['data'] = data
#
#            # find any requests params passed and apply them
#            if 'requests_params' in kwargs['data']:
#                # merge requests params into kwargs
#                kwargs.update(kwargs['data']['requests_params'])
#                del (kwargs['data']['requests_params'])
#
#        if signed:
#            # generate signature
#            kwargs['data']['timestamp'] = self.get_adjusted_time()
#            kwargs['data']['signature'] = self._generate_signature(kwargs['data'])
#
#        # sort get and post params to match signature order
#        if data:
#            # sort post params
#            kwargs['data'] = self._order_params(kwargs['data'])
#            # Remove any arguments with values of None.
#            null_args = [i for i, (key, value) in enumerate(kwargs['data']) if value is None]
#            for i in reversed(null_args):
#                del kwargs['data'][i]
#
#        # if get request assign data array to params value for requests lib
#        if data and (method == 'get' or force_params):
#            kwargs['params'] = '&'.join('%s=%s' % (data[0], data[1]) for data in kwargs['data'])
#            del (kwargs['data'])
#
#        self.response = getattr(self.session, method)(uri, **kwargs)
#        return self._handle_response()
#
#    def get_adjusted_time(self):
#        local_time = int(time.time() * 1000)
#        new_time = local_time - CustomClient.TIME_DELTA
#        adjusted_time = local_time if CustomClient.TIME_DELTA is None else new_time
#        if CustomClient.TIME_DELTA:
#            logging.debug("[CLIENT] Adjusting local timestamp {} by {}ms to: {}".format(
#                local_time,
#                CustomClient.TIME_DELTA,
#                new_time))
#        return adjusted_time
#
#
#class Binance(Series, Order):
#
#    def __init__(self, symbol: str, base_symbol: str = 'USD',
#                 cache_key_date: Optional[datetime] = None, span: Optional[timedelta] = None):
#        if environ.get('BINANCE_API_KEY') is None:
#            raise RuntimeError("The BINANCE_API_KEY environment variable is not set - this needs to be set "
#                               "to the API KEY for your account from the binance.us site.")
#        self.api_key = environ.get('BINANCE_API_KEY')
#        secret = environ.get('BINANCE_SECRET')
#        self.auth_client = CustomClient(self.api_key, secret, tld='us')
#        self.align_server_and_client_times()
#        super().__init__(symbol, base_symbol, cache_key_date, span)
#        script_dir = os.path.dirname(os.path.realpath(__file__))
#        self.cache_dir = os.path.join(script_dir, '../..', '..', '..', '.cache', 'binance')
#
#    def align_server_and_client_times(self):
#        response = self.auth_client.get_server_time()
#        server_time = int(response['serverTime'])
#        local_time = int(time.time() * 1000)  # delay is from server to here
#        CustomClient.TIME_DELTA = (local_time - server_time)
#        adjusted_time = self.auth_client.get_adjusted_time()
#        assert (adjusted_time - server_time) < 1000.0, \
#            "The time difference between binance server ({}) and adjusted ({}) is too large: {}ms".format(
#                server_time, adjusted_time, adjusted_time - server_time)
#
#    def find_symbol_in_data(self, data, entry):
#        contains = False
#        if "symbols" in data:
#            for entry in data["symbols"]:
#                if (entry["baseAsset"] == self.symbol) or (entry["quoteAsset"] == self.symbol):
#                    contains = True
#                    break
#        # for row in data:
#        #     if row[0] == entry:
#        #         contains = True
#        #         break
#        return contains
#
#    def get_is_listed(self) -> bool:
#        # Binance does not support listed companies (e.g. stock, ETFs, etc.)
#        return False
#
#    def get_is_digital_currency(self) -> bool:
#        data, data_file = self.get_api_response(self.auth_client.get_exchange_info, {})
#        is_digital = False
#        for item in data['symbols']:
#            if 'baseAsset' in item and item['baseAsset'] == self.symbol:
#                is_digital = True
#                break
#        return is_digital
#
#    def get_is_physical_currency(self) -> bool:
#        data, data_file = self.get_api_response(self.auth_client.get_exchange_info, {})
#        is_physical = False
#        if 'symbols' in data:
#            for item in data['symbols']:
#                if 'quoteAsset' in item and item['quoteAsset'] == self.base_symbol:
#                    is_physical = True
#                    break
#        return is_physical
#
#    def place_buy_limit_order(self, quantity: float, price: float):
#        args = {
#            "symbol": self.symbol,
#            "quantity": quantity,
#            "price": price,
#        }
#        if self.asset_type == AssetType.DIGITAL_CURRENCY:
#            raw_response, data_file = self.get_api_response(self.auth_client.order_limit_buy, args)
#        else:
#            raise RuntimeError("Adapter is set with unsupported asset type:{}".format(self.asset_type))
#        data = self.translate_order(raw_response)
#        return data
#
#    def place_sell_limit_order(self, quantity: float, price: float):
#        args = {
#            "symbol": self.symbol,
#            "quantity": quantity,
#            "price": price,
#        }
#        if self.asset_type == AssetType.DIGITAL_CURRENCY:
#            raw_response, data_file = self.get_api_response(self.auth_client.order_limit_sell, args)
#        else:
#            raise RuntimeError("Adapter is set with unsupported asset type:{}".format(self.asset_type))
#        data = self.translate_order(raw_response)
#        return data
#
#    def place_buy_market_order(self, quantity: float):
#        args = {
#            "symbol": self.symbol,
#            "quantity": quantity,
#        }
#        if self.asset_type == AssetType.DIGITAL_CURRENCY:
#            raw_response, data_file = self.get_api_response(self.auth_client.order_market_buy, args)
#        else:
#            raise RuntimeError("Adapter is set with unsupported asset type:{}".format(self.asset_type))
#        data = self.translate_order(raw_response)
#        return data
#
#    def place_sell_market_order(self, quantity: float):
#        args = {
#            "symbol": self.symbol,
#            "quantity": quantity,
#        }
#        if self.asset_type == AssetType.DIGITAL_CURRENCY:
#            raw_response, data_file = self.get_api_response(self.auth_client.order_market_sell, args)
#        else:
#            raise RuntimeError("Adapter is set with unsupported asset type:{}".format(self.asset_type))
#        data = self.translate_order(raw_response)
#        return data
#
#    def place_buy_stop_order(self, quantity: float, price: float):
#        price_round_to = self.get_price_round_to()
#        precise_price = int(price * 10 ** price_round_to) / (10 ** price_round_to)
#        quote_round_to = self.get_quantity_round_to()
#        precise_quantity = int(quantity * 10 ** quote_round_to) / (10 ** quote_round_to)
#        # limit_price = precise_price * 1.1  # limit order would not exist, but it's the only way so we give a 10% buffer
#        # precise_limit_price = int(limit_price * 10 ** price_round_to) / (10 ** price_round_to)
#        args = {
#            "symbol": self.get_indicator_key(),
#            "quantity": precise_quantity,
#            "side": Client.SIDE_BUY,
#            "type": Client.ORDER_TYPE_TAKE_PROFIT_LIMIT,
#            "price": precise_price,  # precise_limit_price,
#            "stopPrice": precise_price,
#            "timeInForce": Client.TIME_IN_FORCE_GTC,
#        }
#        if self.asset_type == AssetType.DIGITAL_CURRENCY:
#            raw_response, data_file = self.get_api_response(self.auth_client.create_order, args, cache=False)
#        else:
#            raise RuntimeError("Adapter is set with unsupported asset type:{}".format(self.asset_type))
#        data = self.translate_order(raw_response)
#        return data
#
#    def get_price_round_to(self):
#        return 2
#
#    def get_quantity_round_to(self):
#        return 2
#
#    def place_sell_stop_order(self, quantity: float, price: float):
#        price_round_to = self.get_price_round_to()
#        precise_price = int(price * 10 ** price_round_to) / 10 ** price_round_to
#        quote_round_to = self.get_quantity_round_to()
#        precise_quantity = int(quantity * 10 ** quote_round_to) / 10 ** quote_round_to
#        limit_price = precise_price * 0.9  # limit order would not exist, but it's the only way so we give a 10% buffer
#        precise_limit_price = int(limit_price * 10 ** price_round_to) / (10 ** price_round_to)
#        args = {
#            "symbol": self.get_indicator_key(),
#            "quantity": precise_quantity,
#            "side": Client.SIDE_SELL,
#            "type": Client.ORDER_TYPE_STOP_LOSS_LIMIT,
#            "price": precise_limit_price,
#            "stopPrice": precise_price,
#            "timeInForce": Client.TIME_IN_FORCE_GTC,
#        }
#        if self.asset_type == AssetType.DIGITAL_CURRENCY:
#            raw_response, data_file = self.get_api_response(self.auth_client.create_order, args, cache=False)
#        else:
#            raise RuntimeError("Adapter is set with unsupported asset type:{}".format(self.asset_type))
#        data = self.translate_order(raw_response)
#        return data
#
#    def translate_order(self, response_data):
#        translated = {}
#        assert response_data is not None, "Received a None item while translating response data"
#        dt = datetime.fromtimestamp(float(response_data['transactTime']) / 1000.0)
#        translated[dt] = {}
#        order_id = response_data['orderId']
#        args = {
#            "symbol": self.get_indicator_key(),
#            "orderId": order_id,
#        }
#        raw_response, data_file = self.get_api_response(self.auth_client.get_order, args, cache=False)
#        translated[dt][QueryType.ORDERING] = {}
#        translated[dt][QueryType.ORDERING]['price'] = raw_response['price']
#        translated[dt][QueryType.ORDERING]['quantity'] = raw_response['origQty']
#        logging.info('Order ID is: {}'.format(raw_response['orderId']))
#        logging.info('Order status is: {}'.format(raw_response['status']))
#        logging.info('Order is working: {}'.format(raw_response['isWorking']))
#        return translated
#
#    # def get_stock_series_response(self):
#    #     args = {
#    #         "apikey": self.api_key,
#    #         "symbol": self.symbol,
#    #         "interval": self.translate_interval(),
#    #     }
#    #     raw_response, data_file = self.get_api_response(rs.robinhood.get_stock_historicals, args)
#    #     data = self.translate(raw_response)
#    #     return data
#
#    def translate_interval(self):
#        if self.series_interval == TimeInterval.MIN1:
#            interval = Client.KLINE_INTERVAL_1MINUTE
#            # interval = Client.KLINE_INTERVAL_3MINUTE
#        elif self.series_interval == TimeInterval.MIN5:
#            interval = Client.KLINE_INTERVAL_5MINUTE
#        elif self.series_interval == TimeInterval.MIN15:
#            interval = Client.KLINE_INTERVAL_15MINUTE
#        elif self.series_interval == TimeInterval.MIN30:
#            interval = Client.KLINE_INTERVAL_30MINUTE
#        elif self.series_interval == TimeInterval.HOUR:
#            interval = Client.KLINE_INTERVAL_1HOUR
#            # interval = Client.KLINE_INTERVAL_2HOUR
#            # interval = Client.KLINE_INTERVAL_4HOUR
#        elif self.series_interval == TimeInterval.HOUR6:
#            interval = Client.KLINE_INTERVAL_6HOUR
#            # interval = Client.KLINE_INTERVAL_8HOUR
#            # interval = Client.KLINE_INTERVAL_12HOUR
#        elif self.series_interval == TimeInterval.DAY:
#            interval = Client.KLINE_INTERVAL_1DAY
#            # interval = Client.KLINE_INTERVAL_3DAY
#        elif self.series_interval == TimeInterval.WEEK:
#            interval = Client.KLINE_INTERVAL_1WEEK
#        elif self.series_interval == TimeInterval.MONTH:
#            interval = Client.KLINE_INTERVAL_1MONTH
#        else:
#            raise RuntimeError('Interval is not supported: {} (for: {})'.format(self.series_interval,
#                                                                                Binance.__name__))
#        return interval
#
#    def translate(self, response_data, data_date_format='%Y-%m-%dT%H:%M:%SZ') -> Dict[datetime, Dict[ValueType, float]]:
#        translated = {}
#        assert response_data, "The response data was empty"
#        for item in response_data:
#            assert item is not None, "Received a None item while translating response data"
#            dt = datetime.strptime(item['begins_at'], data_date_format)
#            translated[dt] = {}
#            for value_type in ValueType:
#                value = self.get_response_value_or_none(item, value_type)
#                if value is not None:
#                    ratio = self.get_adjusted_ratio(item)
#                    value = value * ratio
#                    translated[dt][value_type] = value
#        return translated
#
#    def get_digital_series_response(self):
#        # limit = 1000
#        start_at = self.cache_key_date - timedelta(weeks=8)
#        # end_at = self.cache_key_date
#        # start_at = end_at - limit * self.series_interval.timedelta
#        args = {
#            "symbol": "BNBBTC",
#            "interval": Client.KLINE_INTERVAL_1MINUTE,
#            "start_str": "1 day ago UTC",
#            # # "apikey": self.api_key,
#            # "symbol": self.get_indicator_key(),  # '{}{}'.format(self.symbol, self.base_symbol),
#            # "interval": Client.KLINE_INTERVAL_1DAY,  # self.translate_interval(),
#            # # "limit": limit,
#            # # "start_str": start_at.strftime('%s'),
#            # "start_str": int(start_at.strftime('%s')) * 1000,
#        }
#        raw_response, data_file = self.get_api_response(self.auth_client.get_historical_klines, args)
#        assert raw_response, "The response data was empty"
#        data = self.translate_series(raw_response)
#        return data
#
#    def get_indicator_key(self):
#        self.calculate_asset_type()
#        indicator_key = self.symbol
#        if self.asset_type == AssetType.DIGITAL_CURRENCY:
#            indicator_key = "{}{}".format(self.symbol, self.base_symbol)  # e.g. BTC-USD
#        return indicator_key
#
#    def get_holdings(self) -> Dict[str, float]:
#        args = {
#        }
#        raw_response, data_file = self.get_api_response(self.auth_client.get_account, args, cache=False)
#        assert raw_response, "The response data was empty"
#        assert 'balances' in raw_response, "The response data did not have balances"
#        data = {
#        }
#        for balance in raw_response['balances']:
#            locked = float(balance['locked'])
#            if locked != 0.0:
#                logging.info("There is a locked amount for asset '{}' of: {}".format(balance['asset'], locked))
#            data[balance['asset']] = float(balance['free'])
#        return data
#
#    def get_historic_value(self, series_adapter: Series = None) -> Dict[datetime, float]:
#        # args = {
#        #     "symbol": self.get_indicator_key(),
#        # }
#        # raw_response, data_file = self.get_api_response(self.auth_client.get_all_orders, args, cache=False)
#        # assert raw_response, "The response data was empty"
#        data: Dict[datetime, float] = {}
#        holdings = self.get_holdings()
#        series_adapter = self if series_adapter is None else series_adapter
#        closes = series_adapter.get_column(ValueType.CLOSE)
#        # Since Binance doesn't seem to give a nice API to see account value overtime, or even get all trades for all
#        # Symbols, we instead use the current holdings and just use those quantities as the starting value:
#        # NOTE: Binance will give trades per symbol, so we could query all symbols for action
#        for symbol, quantity in holdings.items():
#            if quantity == 0.0:
#                continue
#            for dt, close_value in closes.items():
#                if dt not in data:
#                    data[dt] = 0.0
#                data[dt] += quantity * close_value
#        return data
#
#    @staticmethod
#    def translate_portfolio(response_data, data_date_format='%Y-%m-%dT%H:%M:%SZ') -> Dict[datetime, float]:
#        translated: Dict[datetime, float] = {}
#        assert response_data, "The response data was empty"
#        for item in response_data:
#            assert item is not None, "Received a None item while translating response data"
#            dt = datetime.strptime(item['begins_at'], data_date_format)
#            translated[dt] = float(item['adjusted_close_equity'])
#        return translated
#
#    def get_open_orders(self):
#        args = {
#        }
#        raw_response, data_file = self.get_api_response(self.auth_client.get_open_orders, args, cache=False)
#        orders = []
#        for item in raw_response:
#            side = OrderSide.BUY if item['side'] == Client.SIDE_BUY else OrderSide.SELL
#            dt = datetime.fromtimestamp(float(item['time']) / 1000.0)
#            # data_date_format = '%Y-%m-%dT%H:%M:%S.%f%z'
#            # dt = datetime.strptime(item['time'], data_date_format)
#            args = {
#            }
#            pair_response, pair_file = self.get_api_response(self.auth_client.get_exchange_info, args)
#            symbol = None
#            for pair_item in pair_response['symbols']:
#                if pair_item['symbol'] == item['symbol']:
#                    symbol = pair_item['baseAsset']
#            if item['type'] == Client.ORDER_TYPE_LIMIT:
#                orders.append(LimitOrder(symbol, side, float(item['price']), float(item['quantity']), dt))
#            # elif item['type'] == Client.ORDER_TYPE_STOP_LOSS:  # this order type doesn't work so we are using stop-limit instead
#            # TODO: Add proper support for StopLimit?
#            elif item['type'] == Client.ORDER_TYPE_STOP_LOSS_LIMIT:
#                orders.append(StopOrder(symbol, side, float(item['stopPrice']), float(item['origQty']), dt))
#            else:
#                raise RuntimeError("Unsupported order type: {}".format(item['type']))
#        return orders
#
#    # def translate_orders(self, raw_response, info_api):
#    #     orders = []
#    #     for item in raw_response:
#    #         side = OrderSide.BUY if item['side'] == 'buy' else OrderSide.SELL
#    #         data_date_format = '%Y-%m-%dT%H:%M:%S.%f%z'
#    #         dt = datetime.strptime(item['created_at'], data_date_format)
#    #         order_id = item['id']
#    #         order_info = self.get_order_info(info_api, order_id)
#    #         if item['type'] == 'limit':
#    #             orders.append(LimitOrder(order_info['symbol'], side, float(item['price']), float(item['quantity']), dt))
#    #         elif item['type'] == 'stop':
#    #             orders.append(LimitOrder(order_info['symbol'], side, float(item['price']), float(item['quantity']), dt))
#    #         else:
#    #             raise RuntimeError("Unsupported order type: {}".format(item['type']))
#    #     return orders
#    #
#    # def get_order_info(self, info_api, order_id):
#    #     if info_api == rs.robinhood.get_stock_order_info:
#    #         args = {'orderID': order_id}
#    #     else:
#    #         args = {'order_id': order_id}
#    #     raw_response, data_file = self.get_api_response(info_api, args, cache=False)
#    #     return raw_response
#