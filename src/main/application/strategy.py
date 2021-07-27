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


import inspect
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from main.application.adapter import Adapter, AssetType
from main.application.adapter_collection import AdapterCollection, set_all_cache_key_dates
from main.application.argument import Argument, ArgumentType
from main.application.order import Order
from main.application.value_type import ValueType
from main.common.time_zones import TimeZones
from main.portfolio.portfolio import Portfolio


class MultipleMatchingAdaptersException(RuntimeError):
    pass


class Strategy:
    title: str
    collection: AdapterCollection
    portfolio: Portfolio

    def __init__(self, title: str, portfolio: Portfolio):
        self.collection: AdapterCollection = AdapterCollection()
        self.portfolio = portfolio
        self.title = title
        # self.title += "" if self.portfolio.start_time is None else " starting {}".format(self.portfolio.start_time)
        # self.title += "" if self.portfolio.end_time is None else " ending {}".format(self.portfolio.end_time)
        # self.title += "" if self.portfolio.interval is None else " {}".format(self.portfolio.interval.value)
        self.portfolio.title = self.get_title_with_times()

    def __str__(self):
        return self.get_title_with_times()

    def get_title_with_times(self) -> str:
        string = self.title
        date_format: str = '%Y-%m-%d'
        string += "" if self.portfolio.start_time is None else " starting {}".format(self.portfolio.start_time)
        string += "" if self.portfolio.end_time is None else " ending {}".format(self.portfolio.end_time)
        string += "" if self.portfolio.interval is None else " {}".format(self.portfolio.interval)
        return string

    def run(self):
        key_date = self.portfolio.end_time if self.portfolio.end_time is not None else datetime.now(TimeZones.get_tz())
        set_all_cache_key_dates(self.collection.adapters, key_date)
        self.collection.retrieve_all_data()
        self.portfolio.set_remaining_times(self.collection)
        logging.info("-- Starting strategy: {}".format(self))
        while True:
            remaining_times = self.portfolio.get_remaining_times()
            if not remaining_times:
                logging.info("No more dates left - ending")
                break
            current_time = remaining_times[0]
            self.portfolio.run_to(self.collection, current_time)
            self.next_step(current_time)
        self.portfolio.summarize()
        return self

    def add_collections(self) -> None:
        raise RuntimeError("Implement: {}".format(inspect.currentframe().f_code.co_name))

    def next_step(self, current_time: datetime) -> None:
        raise RuntimeError("Implement: {}".format(inspect.currentframe().f_code.co_name))

    def get_last_start_time(self) -> Optional[datetime]:
        return self.collection.get_common_start_time()

    def get_end_time(self) -> Optional[datetime]:
        return self.collection.get_end_time(symbol)

    def place_open_orders(self):
        for order in self.portfolio.open_orders:
            answer = input("\nDo you want to place the following order?\n> {}\n(y/[n]):".format(order))
            if (answer.lower() == "y") or (answer.lower() == "yes"):
                logging.info("Will now place order...")
                data_adapter = self.collection.get_symbol_handle(order.symbol).adapters[QueryType.ORDERING]
                order.place(data_adapter)
            else:
                logging.info("Order will not be placed.")

    def sync_portfolio_with_account(self):
        self.portfolio.quantities = {}
        self.collection.retrieve_all_data()
        for symbol_adapter in self.collection.symbol_handles.values():
            order_adapter: Order = symbol_adapter.adapters[QueryType.ORDERING]
            holdings = order_adapter.get_holdings()
            self.portfolio.quantities = merge(self.portfolio.quantities)
            self.portfolio.data = order_adapter.get_historic_value(symbol_adapter.adapters[QueryType.SERIES])

    def get_adapter(self, symbol: str, adapter_class: type, value_type: ValueType, asset_type: AssetType,
                    cache_key_date: Optional[datetime] = None) -> Adapter:
        group_adapters = True  # We can remove this, but leaving for now as we may want to make this configurable
        matching_adapters = [adapter for adapter in self.collection.adapters if (adapter.symbol == symbol) and
                             (not group_adapters or (adapter_class == type(adapter)))]
        if len(matching_adapters) == 1:
            adapter: Adapter = matching_adapters[0]
            # adapter.add_value_type(value_type)
        elif len(matching_adapters) == 0:
            adapter: Adapter = adapter_class(symbol, asset_type)
            # adapter.add_value_type(value_type)
            if cache_key_date is not None:
                adapter.cache_key_date = cache_key_date
            self.collection.adapters.append(adapter)
        else:
            raise MultipleMatchingAdaptersException("Only one adapter is allowed to be defined given a symbol and a "
                                                    "value type. For symbol {} found {} adapters that support value "
                                                    "type {}: {}".format(symbol,
                                                                         len(matching_adapters),
                                                                         value_type,
                                                                         matching_adapters))
        return adapter

    def add_price_collection(self, symbol: str, cache_key_date: Optional[datetime] = None) -> None:
        asset_type = self.collection.asset_type_overrides[symbol] if symbol in \
                                                                     self.collection.asset_type_overrides else None
        value_types = [ValueType.OPEN, ValueType.HIGH, ValueType.LOW, ValueType.CLOSE]
        adapters: Dict[ValueType, Any] = {}
        for value_type in value_types:
            adapters[value_type] = self.portfolio.get_adapter_class(value_type)
        for value_type, adapter_class in adapters.items():
            adapter: Adapter = self.get_adapter(symbol, adapter_class, value_type, asset_type, cache_key_date)
            adapter.arguments.append(Argument(ArgumentType.INTERVAL, self.portfolio.interval))
            adapter.arguments.append(Argument(ArgumentType.START_TIME, self.portfolio.start_time))
            adapter.arguments.append(Argument(ArgumentType.END_TIME, self.portfolio.end_time))
            adapter.add_value_type(value_type)

    def add_sma_collection(self, symbol: str, period: str, cache_key_date: Optional[datetime] = None) -> None:
        asset_type = self.collection.asset_type_overrides[symbol] if symbol in \
                                                                          self.collection.asset_type_overrides else None
        value_types = [ValueType.SMA]
        adapters: Dict[ValueType, Any] = {}
        for value_type in value_types:
            adapters[value_type] = self.portfolio.get_adapter_class(value_type)
        for value_type, adapter_class in adapters.items():
            adapter: Adapter = self.get_adapter(symbol, adapter_class, value_type, asset_type, cache_key_date)
            adapter.arguments.append(Argument(ArgumentType.INTERVAL, self.portfolio.interval))
            adapter.arguments.append(Argument(ArgumentType.START_TIME, self.portfolio.start_time))
            adapter.arguments.append(Argument(ArgumentType.END_TIME, self.portfolio.end_time))
            adapter.arguments.append(Argument(ArgumentType.SMA_PERIOD, period))
            adapter.add_value_type(value_type)

    def add_macd_collection(self, symbol, slow, fast, signal, cache_key_date: Optional[datetime] = None):
        asset_type = self.collection.asset_type_overrides[symbol] if symbol in \
                                                                          self.collection.asset_type_overrides else None
        value_types = [ValueType.MACD, ValueType.MACD_HIST, ValueType.MACD_SIGNAL]
        adapters: Dict[ValueType, Any] = {}
        for value_type in value_types:
            adapters[value_type] = self.portfolio.get_adapter_class(value_type)
        for value_type, adapter_class in adapters.items():
            adapter: Adapter = self.get_adapter(symbol, adapter_class, value_type, asset_type, cache_key_date)
            adapter.arguments.append(Argument(ArgumentType.INTERVAL, self.portfolio.interval))
            adapter.arguments.append(Argument(ArgumentType.START_TIME, self.portfolio.start_time))
            adapter.arguments.append(Argument(ArgumentType.END_TIME, self.portfolio.end_time))
            adapter.arguments.append(Argument(ArgumentType.MACD_SLOW, slow))
            adapter.arguments.append(Argument(ArgumentType.MACD_FAST, fast))
            adapter.arguments.append(Argument(ArgumentType.MACD_SIGNAL, signal))
            adapter.add_value_type(value_type)
            # self.collection.adapters.append(adapter)

    def add_rsi_collection(self, symbol, period, cache_key_date: Optional[datetime] = None):
        asset_type = self.collection.asset_type_overrides[symbol] if symbol in \
                                                                          self.collection.asset_type_overrides else None
        value_types = [ValueType.RSI]
        adapters: Dict[ValueType, Any] = {}
        for value_type in value_types:
            adapters[value_type] = self.portfolio.get_adapter_class(value_type)
        for value_type, adapter_class in adapters.items():
            adapter: Adapter = self.get_adapter(symbol, adapter_class, value_type, asset_type, cache_key_date)
            # adapter: Adapter = data_adpter_class(self.symbol, asset_type)
            # if cache_key_date is not None:
            #     adapter.cache_key_date = cache_key_date
            adapter.arguments.append(Argument(ArgumentType.INTERVAL, self.portfolio.interval))
            adapter.arguments.append(Argument(ArgumentType.START_TIME, self.portfolio.start_time))
            adapter.arguments.append(Argument(ArgumentType.END_TIME, self.portfolio.end_time))
            adapter.arguments.append(Argument(ArgumentType.RSI_PERIOD, period))
            adapter.add_value_type(value_type)
            # self.collection.adapters.append(adapter)

    def add_book_collection(self, symbol, period, cache_key_date: Optional[datetime] = None):
        asset_type = self.collection.asset_type_overrides[symbol] if symbol in \
                                                                          self.collection.asset_type_overrides else None
        value_types = [ValueType.BOOK]
        adapters: Dict[ValueType, Any] = {}
        for value_type in value_types:
            adapters[value_type] = self.portfolio.get_adapter_class(value_type)
        for value_type, adapter_class in adapters.items():
            adapter: Adapter = adapter_class(symbol, asset_type)
            if cache_key_date is not None:
                adapter.cache_key_date = cache_key_date
            adapter.arguments.append(Argument(ArgumentType.INTERVAL, self.portfolio.interval))
            adapter.arguments.append(Argument(ArgumentType.START_TIME, self.portfolio.start_time))
            adapter.arguments.append(Argument(ArgumentType.END_TIME, self.portfolio.end_time))
            adapter.arguments.append(Argument(ArgumentType.BOOK, period))
            adapter.add_value_type(value_type)
            # self.collection.adapters.append(adapter)

#     @staticmethod
#     def run(self):
#         portfolio = Strategies.createPortfolio(adapter, symbol, 'SMA {} crossing {}'.format(longCount, shortCount))
#         shortData = adapter.getSmaData(symbol, shortCount, SeriesType.CLOSE)
#         longData = adapter.getSmaData(symbol, longCount, SeriesType.CLOSE)
#         longCount = float(longCount)
#         shortCount = float(shortCount)
#         shortResult = {}
#         shortPrice = 0.0
#         longResult = {}
#         longPrice = 0.0
#         while 1:
#             if shortData.hasTime(portfolio.time):
#                 shortPrice = shortData.getPrice(portfolio.time, SeriesType.SMA)
#                 shortResult[portfolio.time] = shortPrice
#             if longData.hasTime(portfolio.time):
#                 longPrice = longData.getPrice(portfolio.time, SeriesType.SMA)
#                 longResult[portfolio.time] = longPrice
#             if adapter.hasTime(symbol, portfolio.time):
#                 closingPrice = adapter.getPrice(symbol, portfolio.time, SeriesType.CLOSE)
#                 hasPosition = symbol in portfolio.quantities and (portfolio.quantities[symbol] > 0.0)
#                 if (shortPrice >= longPrice) and (portfolio.cash > 0.0):
#                     portfolio.doPurchase(symbol, portfolio.time, closingPrice, portfolio.cash, 'sma short({}): {}
#                     long({}): {}'.format(shortCount, shortPrice, longCount, longPrice))
#                 elif (shortPrice <= longPrice) and hasPosition:
#                     portfolio.doSell(symbol, portfolio.time, closingPrice, portfolio.quantities[symbol],
#                     'sma short({}): {}  long({}): {}'.format(shortCount, shortPrice, longCount, longPrice))
#                 else:
#                     portfolio.incrementTime()
#             else:
#                 portfolio.incrementTime()
#             if portfolio.time >= portfolio.endTime:
#                 break
#         portfolio.addExtra(Extra('ShortSMA', shortResult, '#afa'))
#         portfolio.addExtra(Extra('LongSMA', longResult, '#faa'))
#         portfolio.calculateRoi()
#         return portfolio

#     @staticmethod
#     def run(self):
#         portfolio = Strategies.createPortfolio(adapter, symbol, 'Trailing Buy {} and Sell {} RSI {} to {} period {
#         }'.format(buyAt, sellAt, upper, lower, timePeriod))
#         upper = float(upper)
#         lower = float(lower)
#         rsiData = adapter.getRsiData(symbol, timePeriod, SeriesType.CLOSE)
#         rsiResult = {}
#         rsiPrice = 0.0
#         while 1:
#             if rsiData.hasTime(portfolio.time):
#                 rsiPrice = rsiData.getPrice(portfolio.time, SeriesType.RSI)
#                 rsiResult[portfolio.time] = rsiPrice
#             if adapter.hasTime(symbol, portfolio.time):
#                 hasPosition = symbol in portfolio.quantities and (portfolio.quantities[symbol] > 0.0)
#                 if (portfolio.cash > 0.0):
#                     moreToGo = False
#                     portfolio.trailingHigh = None
#                     portfolio.trailingLow = None
#                     portfolio.nextBuyPrice = portfolio.lastSellPrice * buyAt
#                     if (portfolio.cash <= 0.0):
#                         moreToGo = True
#                     while not moreToGo and portfolio.stepToNext(symbol):
#                         if rsiData.hasTime(portfolio.time):
#                             rsiPrice = rsiData.getPrice(portfolio.time, SeriesType.RSI)
#                             rsiResult[portfolio.time] = rsiPrice
#                         portfolio.nextBuyPrice = portfolio.trailingHigh * buyAt
#                         if (rsiPrice <= lower) and (portfolio.periodLow <= portfolio.nextBuyPrice):
#                             portfolio.doPurchase(symbol, portfolio.time, portfolio.nextBuyPrice, portfolio.cash,
#                             'trailing final:{:0.2f} -> buy:{:0.2f}'.format(portfolio.trailingHigh,
#                             portfolio.nextBuyPrice))
#                             moreToGo = True
#                             break
#                         portfolio.endStep()
#                     if not moreToGo:
#                         break
#                 elif hasPosition:
#                     moreToGo = False
#                     portfolio.trailingHigh = None
#                     portfolio.trailingLow = None
#                     portfolio.nextSellPrice = portfolio.lastBuyPrice * sellAt
#                     if (portfolio.quantities[symbol] <= 0.0):
#                         moreToGo = True
#                     while not moreToGo and portfolio.stepToNext(symbol):
#                         if rsiData.hasTime(portfolio.time):
#                             rsiPrice = rsiData.getPrice(portfolio.time, SeriesType.RSI)
#                             rsiResult[portfolio.time] = rsiPrice
#                         portfolio.nextSellPrice = portfolio.periodLow * sellAt
#                         if (rsiPrice >= upper) and (portfolio.periodHigh >= portfolio.nextSellPrice):
#                             portfolio.doSell(symbol, portfolio.time, portfolio.nextSellPrice, portfolio.quantities[
#                             symbol], 'trailing final:{:0.2f} -> sell:{:0.2f}'.format(portfolio.trailingLow,
#                             portfolio.nextSellPrice))
#                             moreToGo = True
#                             break
#                         portfolio.endStep()
#                     if not moreToGo:
#                         break
#                 else:
#                     portfolio.incrementTime()
#             else:
#                 portfolio.incrementTime()
#             if portfolio.time >= portfolio.endTime:
#                 break
#         portfolio.nextMessage = '--> Last RSI: {} (buy <= {} and sell >= {})'.format(rsiPrice, lower, upper)
#         portfolio.addExtra(Extra('RSI', rsiResult, '#aaa', priceBased=False))
#         portfolio.calculateRoi()
#         return portfolio

#     @staticmethod
#     def run(self):
#         portfolio = Strategies.createPortfolio(adapter, symbol, 'Trailing Buy {} and Sell {} Dip {}'.format(buyAt,
#         sellStart, sellDip))
#         trailingResult = {}
#         while 1:
#             if (not portfolio.buyNextDipTrailing(symbol, buyAt, portfolio.cash, trailingResult)):
#                 break
#             abovePrice = portfolio.lastBuyPrice * sellStart
#             if (not portfolio.sellNextDipAbove(symbol, abovePrice, sellDip, portfolio.quantities[symbol],
#             trailingResult)):
#                 break
#         portfolio.addExtra(Extra('Trailing', trailingResult, '#00f'))
#         portfolio.calculateRoi()
#         return portfolio
