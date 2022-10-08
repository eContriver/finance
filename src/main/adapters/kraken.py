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
# import os.path
# import time
# from datetime import datetime, timedelta
# from os import environ
# from typing import Optional
#
# import cbpro
# from cbpro import OrderBook
#
# from main.adapters.orders.orderBook import OrderBook
# from main.adapters.adapter import TimeInterval, AssetType
# from main.adapters.valueType import ValueType
# from main.adapters.calculators.series import Series
# from main.adapters.orders.order import Order
#
# from pymongo import MongoClient
#
# class MyWebsocketClient(cbpro.WebsocketClient):
#     def on_open(self):
#         self.url = "wss://ws-feed.pro.coinbase.com/"
#         self.products = ["ETH-USD"]
#         self.message_count = 0
#         # self.message_type = "subscribe"
#         mongo_client = MongoClient('mongodb://localhost:27017/')
#         db = mongo_client.coinbase_pro_db
#         self.mongo_collection = db.ETH_book_collection
#         # self.should_print = True
#         # self.auth = False
#         # self.api_key = ""
#         # self.api_secret = ""
#         # self.api_passphrase = ""
#         self.channels = ["level2"]
#         # message_type="subscribe",
#         # mongo_collection=None,
#         # should_print=True,
#         # auth=False,
#         # api_key="",
#         # api_secret="",
#         # api_passphrase="",
#         # channels = ["level2"]
#         print("Lets count the messages!")
#
#     def on_message(self, msg):
#         self.message_count += 1
#         print("Message: {}".format(msg))
#         if 'price' in msg and 'type' in msg:
#             print("Message type:", msg["type"], "\t@ {:.3f}".format(float(msg["price"])))
#
#     def on_close(self):
#         print("-- Goodbye! --")
#
#
# class OrderBookConsole(OrderBook):
#     ''' Logs real-time changes to the bid-ask spread to the console '''
#
#     def __init__(self, product_id=None):
#         super(OrderBookConsole, self).__init__(product_id=product_id)
#
#         # latest values of bid-ask spread
#         self._bid = None
#         self._ask = None
#         self._bid_depth = None
#         self._ask_depth = None
#
#     def on_message(self, message):
#         super(OrderBookConsole, self).on_message(message)
#
#         # Calculate newest bid-ask spread
#         bid = self.get_bid()
#         bids = self.get_bids(bid)
#         bid_depth = sum([b['size'] for b in bids])
#         ask = self.get_ask()
#         asks = self.get_asks(ask)
#         ask_depth = sum([a['size'] for a in asks])
#
#         if self._bid == bid and self._ask == ask and self._bid_depth == bid_depth and self._ask_depth == ask_depth:
#             # If there are no changes to the bid-ask spread since the last update, no need to print
#             pass
#         else:
#             # If there are differences, update the cache
#             self._bid = bid
#             self._ask = ask
#             self._bid_depth = bid_depth
#             self._ask_depth = ask_depth
#             print('{} {} bid: {:.3f} @ {:.2f}\task: {:.3f} @ {:.2f}'.format(
#                 datetime.now(), self.product_id, bid_depth, bid, ask_depth, ask))
#             # logging.info('{} {} bid: {:.3f} @ {:.2f}\task: {:.3f} @ {:.2f}'.format(
#             #     datetime.now(), self.product_id, bid_depth, bid, ask_depth, ask))
#
#
# class Kraken(Series, Order, OrderBook):
#
#     def __init__(self, symbol: str, base_symbol: str = 'USD',
#                  cache_key_date: Optional[datetime] = None, span: Optional[timedelta] = None):
#         if environ.get('COINBASE_API_KEY') is None:
#             raise RuntimeError("The COINBASE_API_KEY environment variable is not set - this needs to be set to the API KEY for your account from the coinbase.com site.")
#         api_key = environ.get('COINBASE_API_KEY')
#         if environ.get('COINBASE_SECRET') is None:
#             raise RuntimeError("The COINBASE_SECRET environment variable is not set - this needs to be set to the API KEY for your account from the coinbase.com site.")
#         b64secret = environ.get('COINBASE_SECRET')
#         if environ.get('COINBASE_PASSPHRASE') is None:
#             raise RuntimeError("The COINBASE_PASSPHRASE environment variable is not set - this needs to be set to the API KEY for your account from the coinbase.com site.")
#         passphrase = environ.get('COINBASE_PASSPHRASE')
#         self.public_client = cbpro.PublicClient()
#         self.auth_client = cbpro.AuthenticatedClient(api_key, b64secret, passphrase)
#         super().__init__(symbol, base_symbol, cache_key_date)
#         script_dir = os.path.dirname(os.path.realpath(__file__))
#         self.cache_dir = os.path.join(script_dir, '../..', '..', '..', '.cache', 'coinbasePro')
#
#     def find_symbol_in_data(self, data, entry):
#         contains = False
#         if "symbols" in data:
#             for entry in data["symbols"]:
#                 if (entry["baseAsset"] == self.symbol) or (entry["quoteAsset"] == self.symbol):
#                     contains = True
#                     break
#         # for row in data:
#         #     if row[0] == entry:
#         #         contains = True
#         #         break
#         return contains
#
#     def get_is_listed(self) -> bool:
#         # Binance does not support listed companies (e.g. stock, ETFs, etc.)
#         return False
#
#     def get_is_digital_currency(self) -> bool:
#         return self.symbol_exists(self.symbol)
#
#     def symbol_exists(self, symbol):
#         args = {}
#         data, data_file = self.get_api_response(self.public_client.get_currencies, args)
#         match = False
#         for item in data:
#             if 'id' in item and item['id'] == symbol:
#                 match = True
#                 break
#         return match
#
#     def get_is_physical_currency(self) -> bool:
#         return self.symbol_exists(self.base_symbol)
#
#     # def place_buy_limit_order(self, quantity: float, price: float):
#     #     args = {
#     #         "symbol": self.symbol,
#     #         "quantity": quantity,
#     #         "price": price,
#     #     }
#     #     if self.asset_type == AssetType.DIGITAL_CURRENCY:
#     #         raw_response, data_file = self.get_api_response(self.auth_client.order_limit_buy, args)
#     #     else:
#     #         raise RuntimeError("Adapter is set with unsupported asset type:{}".format(self.asset_type))
#     #     data = self.translate_order(raw_response)
#     #     return data
#
#     # def place_sell_limit_order(self, quantity: float, price: float):
#     #     args = {
#     #         "symbol": self.symbol,
#     #         "quantity": quantity,
#     #         "price": price,
#     #     }
#     #     if self.asset_type == AssetType.DIGITAL_CURRENCY:
#     #         raw_response, data_file = self.get_api_response(self.auth_client.order_limit_sell, args)
#     #     else:
#     #         raise RuntimeError("Adapter is set with unsupported asset type:{}".format(self.asset_type))
#     #     data = self.translate_order(raw_response)
#     #     return data
#
#     # def place_buy_market_order(self, quantity: float):
#     #     args = {
#     #         "symbol": self.symbol,
#     #         "quantity": quantity,
#     #     }
#     #     if self.asset_type == AssetType.DIGITAL_CURRENCY:
#     #         raw_response, data_file = self.get_api_response(self.auth_client.order_market_buy, args)
#     #     else:
#     #         raise RuntimeError("Adapter is set with unsupported asset type:{}".format(self.asset_type))
#     #     data = self.translate_order(raw_response)
#     #     return data
#
#     # def place_sell_market_order(self, quantity: float):
#     #     args = {
#     #         "symbol": self.symbol,
#     #         "quantity": quantity,
#     #     }
#     #     if self.asset_type == AssetType.DIGITAL_CURRENCY:
#     #         raw_response, data_file = self.get_api_response(self.auth_client.order_market_sell, args)
#     #     else:
#     #         raise RuntimeError("Adapter is set with unsupported asset type:{}".format(self.asset_type))
#     #     data = self.translate_order(raw_response)
#     #     return data
#
#     # def place_buy_stop_order(self, quantity: float, price: float):
#     #     price_round_to = self.get_price_round_to()
#     #     precise_price = int(price * 10 ** price_round_to) / 10 ** price_round_to
#     #     quote_round_to = self.get_quantity_round_to()
#     #     precise_quantity = int(quantity * 10 ** quote_round_to) / 10 ** quote_round_to
#     #     limit_price = precise_price * 1.1
#     #     args = {
#     #         "symbol": self.get_indicator_key(),
#     #         "quantity": precise_quantity,
#     #         "side": Client.SIDE_BUY,
#     #         "type": Client.ORDER_TYPE_STOP_LOSS_LIMIT,
#     #         "price": limit_price,
#     #         "stopPrice": precise_price,
#     #         "timeInForce": Client.TIME_IN_FORCE_GTC,
#     #     }
#     #     if self.asset_type == AssetType.DIGITAL_CURRENCY:
#     #         raw_response, data_file = self.get_api_response(self.auth_client.create_test_order, args, cache=False)
#     #     else:
#     #         raise RuntimeError("Adapter is set with unsupported asset type:{}".format(self.asset_type))
#     #     data = self.translate_order(raw_response)
#     #     return data
#
#     def get_price_round_to(self):
#         return 2
#
#     def get_quantity_round_to(self):
#         return 2
#
#     # def place_sell_stop_order(self, quantity: float, price: float):
#     #     price_round_to = self.get_price_round_to()
#     #     precise_price = int(price * 10 ** price_round_to) / 10 ** price_round_to
#     #     quote_round_to = self.get_quantity_round_to()
#     #     precise_quantity = int(quantity * 10 ** quote_round_to) / 10 ** quote_round_to
#     #     limit_price = precise_price * 0.9
#     #     args = {
#     #         "symbol": self.get_indicator_key(),
#     #         "quantity": precise_quantity,
#     #         "side": Client.SIDE_SELL,
#     #         "type": Client.ORDER_TYPE_STOP_LOSS_LIMIT,
#     #         "price": limit_price,
#     #         "stopPrice": precise_price,
#     #         "timeInForce": Client.TIME_IN_FORCE_GTC,
#     #     }
#     #     if self.asset_type == AssetType.DIGITAL_CURRENCY:
#     #         raw_response, data_file = self.get_api_response(self.auth_client.create_order, args, cache=False)
#     #     else:
#     #         raise RuntimeError("Adapter is set with unsupported asset type:{}".format(self.asset_type))
#     #     data = self.translate_order(raw_response)
#     #     return data
#
#     # def translate_order(self, response_data):
#     #     translated = {}
#     #     assert response_data is not None, "Received a None item while translating response data"
#     #     dt = datetime.fromtimestamp(float(response_data['transactTime']) / 1000.0)
#     #     translated[dt] = {}
#     #     order_id = response_data['orderId']
#     #     args = {
#     #         "symbol": self.get_indicator_key(),
#     #         "orderId": order_id,
#     #     }
#     #     raw_response, data_file = self.get_api_response(self.auth_client.get_order, args, cache=False)
#     #     translated[dt][QueryType.ORDERING] = {}
#     #     translated[dt][QueryType.ORDERING]['price'] = raw_response['price']
#     #     translated[dt][QueryType.ORDERING]['quantity'] = raw_response['origQty']
#     #     logging.info('Order ID is: {}'.format(raw_response['orderId']))
#     #     logging.info('Order status is: {}'.format(raw_response['status']))
#     #     logging.info('Order is working: {}'.format(raw_response['isWorking']))
#     #     return translated
#
#     # def get_stock_series_response(self):
#     #     args = {
#     #         "apikey": self.api_key,
#     #         "symbol": self.symbol,
#     #         "interval": self.translate_interval(),
#     #     }
#     #     raw_response, data_file = self.get_api_response(rs.robinhood.get_stock_historicals, args)
#     #     data = self.translate(raw_response)
#     #     return data
#
#     def translate_interval(self):
#         if self.series_interval == TimeInterval.MIN1:
#             interval = 60
#         elif self.series_interval == TimeInterval.MIN5:
#             interval = 300
#         elif self.series_interval == TimeInterval.MIN15:
#             interval = 900
#         elif self.series_interval == TimeInterval.HOUR:
#             interval = 3600
#         elif self.series_interval == TimeInterval.HOUR6:
#             interval = 21600
#         elif self.series_interval == TimeInterval.DAY:
#             interval = 86400
#         else:
#             raise RuntimeError('Interval is not supported: {} (for: {})'.format(self.series_interval,
#                                                                                 CoinbaseProAdapter.__name__))
#         return interval
#
#     def translate_series(self, response_data, data_date_format='%Y-%m-%dT%H:%M:%SZ') -> dict[datetime, dict[ValueType, float]]:
#         translated = {}
#         assert response_data, "The response data was empty"
#         for entry in response_data:
#             dt = datetime.fromtimestamp(entry[0])  # 1612747380
#             translated[dt] = {}
#             translated[dt][ValueType.LOW] = entry[1]
#             translated[dt][ValueType.HIGH] = entry[2]
#             translated[dt][ValueType.OPEN] = entry[3]
#             translated[dt][ValueType.CLOSE] = entry[4]
#             translated[dt][ValueType.VOLUME] = entry[5]
#         # for item in response_data:
#         #     assert item is not None, "Received a None item while translating response data"
#         #     dt = datetime.strptime(item['begins_at'], data_date_format)
#         #     translated[dt] = {}
#         #     for value_type in ValueType:
#         #         value = self.get_value_or_none(item, value_type)
#         #         if value is not None:
#         #             ratio = self.get_adjusted_ratio(item)
#         #             value = value * ratio
#         #             translated[dt][value_type] = value
#         return translated
#
#     def get_digital_series_response(self):
#         args = {}
#         args['granularity'] = self.translate_interval()
#         args['product_id'] = self.get_indicator_key()
#         raw_response, data_file = self.get_api_response(self.public_client.get_product_historic_rates, args)
#         data = self.translate_series(raw_response)
#         return data
#
#     def get_indicator_key(self):
#         self.calculate_asset_type()
#         indicator_key = self.symbol
#         if self.asset_type == AssetType.DIGITAL_CURRENCY:
#             indicator_key = "{}-{}".format(self.symbol, self.base_symbol)  # e.g. BTC-USD
#         return indicator_key
#
#     def get_book_response(self):
#         # 1. Send a subscribe message for the product(s) of interest and the full channel.
#         # 2. Queue any messages received over the websocket stream.
#         # 3. Make a REST request for the order book snapshot from the REST feed.
#         # 4. Playback queued messages, discarding sequence numbers before or equal to the snapshot
#         #    sequence number.
#         # 5. Apply playback messages to the snapshot as needed(see below).
#         # 6. After playback is complete, apply real - time stream messages as they arrive.
#
#         wsClient = MyWebsocketClient()
#         wsClient.start()
#         print(wsClient.url, wsClient.products)
#         while (wsClient.message_count < 500):
#             print("\nmessage_count =", "{} \n".format(wsClient.message_count))
#             time.sleep(1)
#         wsClient.close()
#
#         # self.book = OrderBookConsole(self.get_indicator_key())
#         # self.book.channels = ["level2"]
#         # self.book.start()
#         # time.sleep(10)
#         # self.book.close()
#
#         data = {}
#         # args = {}
#         # args['granularity'] = self.translate_interval()
#         # args['product_id'] = self.get_indicator_key()
#         # raw_response, data_file = self.get_api_response(self.public_client.get_product_order_book, args)
#         # data = self.translate_series(raw_response)
#         return data
#
#     def get_holdings(self) -> dict[str, float]:
#         # args = {
#         # }
#         # raw_response, data_file = self.get_api_response(self.auth_client.get_account, args, cache=False)
#         # assert raw_response, "The response data was empty"
#         # assert 'balances' in raw_response, "The response data did not have balances"
#         data = {
#         }
#         # for balance in raw_response['balances']:
#         #     locked = float(balance['locked'])
#         #     if locked != 0.0:
#         #         logging.info("There is a locked amount for asset '{}' of: {}".format(balance['asset'], locked))
#         #     data[balance['asset']] = float(balance['free'])
#         return data
#
#     def get_historic_value(self, series_adapter: Series = None) -> dict[datetime, float]:
#         # args = {
#         #     "symbol": self.get_indicator_key(),
#         # }
#         # raw_response, data_file = self.get_api_response(self.auth_client.get_all_orders, args, cache=False)
#         # assert raw_response, "The response data was empty"
#         data: dict[datetime, float] = {}
#         # holdings = self.get_holdings()
#         # series_adapter = self if series_adapter is None else series_adapter
#         # closes = series_adapter.get_all_items(ValueType.CLOSE)
#         # # Since Binance doesn't seem to give a nice API to see account value overtime, or even get all trades for all
#         # # Symbols, we instead use the current holdings and just use those quantities as the starting value:
#         # # NOTE: Binance will give trades per symbol, so we could query all symbols for action
#         # for symbol, quantity in holdings.items():
#         #     if quantity == 0.0:
#         #         continue
#         #     for dt, close_value in closes.items():
#         #         if dt not in data:
#         #             data[dt] = 0.0
#         #         data[dt] += quantity * close_value
#         return data
#
#     # @staticmethod
#     # def translate_portfolio(response_data, data_date_format='%Y-%m-%dT%H:%M:%SZ') -> dict[datetime, float]:
#     #     translated: dict[datetime, float] = {}
#     #     assert response_data, "The response data was empty"
#     #     for item in response_data:
#     #         assert item is not None, "Received a None item while translating response data"
#     #         dt = datetime.strptime(item['begins_at'], data_date_format)
#     #         translated[dt] = float(item['adjusted_close_equity'])
#     #     return translated
#
#     def get_open_orders(self):
#         # args = {
#         # }
#         # raw_response, data_file = self.get_api_response(self.auth_client.get_open_orders, args, cache=False)
#         orders = []
#         # for item in raw_response:
#         #     side = OrderSide.BUY if item['side'] == Client.SIDE_BUY else OrderSide.SELL
#         #     dt = datetime.fromtimestamp(float(item['time']) / 1000.0)
#         #     # data_date_format = '%Y-%m-%dT%H:%M:%S.%f%z'
#         #     # dt = datetime.strptime(item['time'], data_date_format)
#         #     args = {
#         #     }
#         #     pair_response, pair_file = self.get_api_response(self.auth_client.get_exchange_info, args)
#         #     symbol = None
#         #     for pair_item in pair_response['symbols']:
#         #         if pair_item['symbol'] == item['symbol']:
#         #             symbol = pair_item['baseAsset']
#         #     if item['type'] == Client.ORDER_TYPE_LIMIT:
#         #         orders.append(LimitOrder(symbol, side, float(item['price']), float(item['quantity']), dt))
#         #     # elif item['type'] == Client.ORDER_TYPE_STOP_LOSS:  # this order type doesn't work so we are using stop-limit instead
#         #     # TODO: Add proper support for StopLimit?
#         #     elif item['type'] == Client.ORDER_TYPE_STOP_LOSS_LIMIT:
#         #         orders.append(StopOrder(symbol, side, float(item['stopPrice']), float(item['origQty']), dt))
#         #     else:
#         #         raise RuntimeError("Unsupported order type: {}".format(item['type']))
#         return orders
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
#     #     if info_api == rs.robinhood.get_stock_order_info:
#     #         args = {'orderID': order_id}
#     #     else:
#     #         args = {'order_id': order_id}
#     #     raw_response, data_file = self.get_api_response(info_api, args, cache=False)
#     #     return raw_response
#
#
# # class KrakenAdapter(DataAdapter):
# #     def __init__(self, cacheDir, dataDate=None):
# #         if environ.get('KRAKEN_API_KEY') is None:
# #             raise RuntimeError("The KRAKEN_API_KEY environment variable is not set - this needs to be set to the
# #             API KEY for your account from the kraken.com site.")
# #         apiKey = environ.get('KRAKEN_API_KEY')
# #         providerCacheDir = os.path.join(cacheDir, 'kraken')
# #         super().__init__(providerCacheDir, apiKey, dataDate)
#
# #     def getRawData(self, endPoint, query={}, dataType=DataType.JSON):
# #         lowerValues = [str(value).lower() for value in query.values()]
# #         lowerValues.append(endPoint.replace('/', '-'))
# #         name = '_'.join(lowerValues)
# #         dataFile = os.path.join(self.cacheDir, 'data_{}_{}.log'.format(name, self.cacheDateKey.strftime('%Y%m%d')))
# #         if not os.path.exists(dataFile):
# #             urlQuery = '&'.join(['%s=%s' % (key, value) for (key, value) in query.items()])
# #             urlQuery = "?" + urlQuery if urlQuery else ""
# #             url = 'https://futures.kraken.com/derivatives/{}{}'.format(endPoint, urlQuery) # self.apiKey
# #             logging.info('Requesting data from: {}'.format(url))
# #             response = requests.get(url)
# #             logging.info('Received response: {}'.format(response))
# #             response.raise_for_status()
# #             fdWrite = open(dataFile, "w")
# #             fdWrite.write(response.text)
# #             fdWrite.close()
# #             logging.info('Data saved to: {}'.format(dataFile))
# #         else:
# #             logging.info('Using cached file: {}'.format(dataFile))
# #         fdRead = open(dataFile, "r")
# #         data = None
# #         if dataType == DataType.JSON:
# #             data = json.load(fdRead)
# #             fdRead.close()
# #             if 'result' not in data:
# #                 raise RuntimeError("Failed to find result in response - {}\n  See: {}".format(data, dataFile))
# #             if 'error' in data:
# #                 raise RuntimeError("Error message in response - {}\n  See: {}".format(data['error'], dataFile))
# #             if (data['result'] == "error"):
# #                 raise RuntimeError("Result was an error in response - {}\n  See: {}".format(data, dataFile))
# #         elif dataType == DataType.CSV:
# #             reader = csv.reader(fdRead, delimiter=',')
# #             data = []
# #             for row in reader:
# #                 data.append(row)
# #             fdRead.close()
# #             if not data:
# #                 raise RuntimeError("List data size is zero, see: {}".format(dataFile))
# #         else:
# #             raise RuntimeError("Unrecognized data type: {}".format(dataType))
# #         return data
#
# #     def getDigitalCurrencyData(self):
# #         return self.getRawData('api/v3/tickers')
#
# # def getPhysicalCurrencyData(self):
# #     return self.getList('physical_currency_list')
#
# # def getListingStatusData(self):
# #     query = {
# #         "function": "LISTING_STATUS",
# #     }
# #     return self.getRawData(query, DataType.CSV)
#
# # def getStockSeriesResponse(self, interval, symbol, market):
# #     if interval == TimeInterval.DAILY:
# #         function = "TIME_SERIES_DAILY_ADJUSTED"
# #         # function = "TIME_SERIES_DAILY"
# #         key = 'Time Series (Daily)'
# #     elif interval == TimeInterval.WEEKLY:
# #         function = "TIME_SERIES_WEEKLY_ADJUSTED"
# #         key = 'Weekly Adjusted Time Series'
# #         # function = "TIME_SERIES_WEEKLY"
# #         # key = 'Weekly Time Series'
# #     elif interval == TimeInterval.MONTHLY:
# #         function = "TIME_SERIES_MONTHLY_ADJUSTED"
# #         # function = "TIME_SERIES_MONTHLY"
# #         key = 'Monthly Time Series'
# #     else:
# #         raise RuntimeError('Unkown interval: {}'.format(interval))
# #     query = {
# #         "function": function,
# #         "symbol": symbol,
# #     }
# #     return ResponseData(self.getRawData(query), key)
#
# # def getDigitalSeriesResponse(self, interval, symbol, market):
# #     if interval == TimeInterval.DAILY:
# #         function = "DIGITAL_CURRENCY_DAILY"
# #         key = 'Time Series (Digital Currency Daily)'
# #     elif interval == TimeInterval.WEEKLY:
# #         function = "DIGITAL_CURRENCY_WEEKLY"
# #         key = 'Time Series (Digital Currency Weekly)'
# #     elif interval == TimeInterval.MONTHLY:
# #         function = "DIGITAL_CURRENCY_MONTHLY"
# #         key = 'Time Series (Digital Currency Monthly)'
# #     else:
# #         raise RuntimeError('Unkown interval: {}'.format(interval))
# #     query = {
# #         "function": function,
# #         "symbol": symbol,
# #         "market": market,
# #     }
# #     return ResponseData(self.getRawData(query), key)
#
# # def getMacdResponse(self, assetType, symbol, slowPeriod, fastPeriod, signalPeriod, seriesType):
# #     indicatorKey = self.getIndicatorKey(symbol, assetType) # e.g. BTCUSD
# #     query = {
# #         "function": "MACD",
# #         "symbol": indicatorKey,
# #         "interval": self.interval.value,
# #         "slowperiod": slowPeriod,
# #         "fastperiod": fastPeriod,
# #         "signalperiod": signalPeriod,
# #         "series_type": seriesType.value,
# #     }
# #     return ResponseData(self.getRawData(query), 'Technical Analysis: MACD')
#
# # def getSmaResponse(self, assetType, symbol, timePeriod, seriesType):
# #     indicatorKey = self.getIndicatorKey(symbol, assetType) # e.g. BTCUSD
# #     query = {
# #         "function": "SMA",
# #         "symbol": indicatorKey,
# #         "interval": self.interval.value,
# #         "time_period": timePeriod,
# #         "series_type": seriesType.value,
# #     }
# #     return ResponseData(self.getRawData(query), 'Technical Analysis: SMA')
#
# # def getIndicatorKey(self, symbol, assetType):
# #     indicatorKey = symbol
# #     if assetType == AssetType.DIGITAL_CURRENCY:
# #         indicatorKey = symbol + self.market # e.g. BTCUSD
# #     return indicatorKey
#
# # def getRsiResponse(self, assetType, symbol, timePeriod, seriesType):
# #     indicatorKey = self.getIndicatorKey(symbol, assetType) # e.g. BTCUSD
# #     query = {
# #         "function": "RSI",
# #         "symbol": indicatorKey,
# #         "interval": self.interval.value,
# #         "time_period": timePeriod,
# #         "series_type": seriesType.value,
# #     }
# #     return ResponseData(self.getRawData(query), 'Technical Analysis: RSI')
#
#
