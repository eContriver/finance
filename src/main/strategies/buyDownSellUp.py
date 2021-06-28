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

from main.adapters.valueType import ValueType
from main.portfolio.order import LimitOrder, OrderSide
from main.portfolio.portfolio import Portfolio
from main.strategies.singleSymbolStrategy import SingleSymbolStrategy


class BuyDownSellUp(SingleSymbolStrategy):
    buy_down: float
    sell_up: float

    def __init__(self, symbol: str, portfolio: Portfolio, buy_down: float, sell_up: float):
        super().__init__("Buy down {:0.2f} Sell up {:0.2f}".format(buy_down, sell_up), symbol, portfolio)
        self.buy_down = buy_down
        self.sell_up = sell_up
        self.build_price_collection()

    def next_step(self, current_time):
        last_time = self.portfolio.get_last_completed_time()
        if len(self.portfolio.open_orders) == 0:
            cash = self.portfolio.quantities[self.collection.get_base_symbol()]
            quantity: float = self.portfolio.quantities[self.symbol]
            if cash > 0.0:
                self.open_limit_buy(cash, current_time, last_time)
            elif quantity > 0.0:
                self.open_limit_sell(current_time, last_time, quantity)
            else:
                raise RuntimeError("No orders are open nor is there any cash nor quantity of symbol")

    def open_limit_sell(self, current_time, last_time, quantity):
        last_time = last_time if last_time is not None else current_time
        last_low = self.collection.get_value(self.symbol, last_time, ValueType.LOW)
        sell_price = self.sell_up * last_low
        order = LimitOrder(self.symbol, OrderSide.SELL, sell_price, quantity, current_time)
        order.message = "price crossed above up {:0.2f} ({:0.2f} * {:0.2f})".format(sell_price, self.sell_up, last_low)
        self.portfolio.open_order(order)

    def open_limit_buy(self, cash, current_time, last_time):
        last_time = last_time if last_time is not None else current_time
        last_high = self.collection.get_value(self.symbol, last_time, ValueType.HIGH)
        buy_price = self.buy_down * last_high
        order = LimitOrder(self.symbol, OrderSide.BUY, buy_price, cash, current_time)
        order.message = "price crossed below down {:0.2f} ({:0.2f} * {:0.2f})".format(buy_price, self.buy_down,
                                                                                      last_high)
        self.portfolio.open_order(order)
