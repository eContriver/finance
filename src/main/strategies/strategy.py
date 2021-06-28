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
from typing import Optional, Set

from main.adapters.adapter import Adapter
from main.adapters.adapterCollection import AdapterCollection
from main.adapters.orders.order import Order
from main.common.profiler import Profiler
from main.portfolio.portfolio import Portfolio


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
        string += "" if self.portfolio.start_time is None else " starting {}".format(self.portfolio.start_time)
        string += "" if self.portfolio.end_time is None else " ending {}".format(self.portfolio.end_time)
        string += "" if self.portfolio.interval is None else " {}".format(self.portfolio.interval)
        return string

    def run(self):
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
        # Profiler.get_instance().report()
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
            self.portfolio.quantities = Adapter.merge(holdings, self.portfolio.quantities)
            self.portfolio.data = order_adapter.get_historic_value(symbol_adapter.adapters[QueryType.SERIES])

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
