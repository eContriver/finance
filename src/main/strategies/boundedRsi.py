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
from datetime import datetime

from main.adapters.valueType import ValueType
from main.portfolio.order import MarketOrder, OrderSide
from main.portfolio.portfolio import Portfolio
from main.strategies.singleSymbolStrategy import SingleSymbolStrategy


class BoundedRsi(SingleSymbolStrategy):
    upper: float
    lower: float
    period: float

    def __init__(self, symbol: str, portfolio: Portfolio, period: float, upper: float, lower: float):
        super().__init__("Bounded RSI upper {:0.2f} lower {:0.2f} period {:0.2f}".format(upper, lower, period), symbol,
                         portfolio)
        self.upper = upper
        self.lower = lower
        self.period = period
        self.build_price_collection()
        self.build_rsi_collection(symbol, self.period)

    def next_step(self, current_time):
        last_time = self.portfolio.get_last_completed_time()
        if last_time is not None:
            cash = self.portfolio.quantities[self.collection.get_base_symbol()]
            quantity: float = self.portfolio.quantities[self.symbol]
            closest_time = self.collection.get_adapter(self.symbol, ValueType.RSI).find_closest_before_else_after(last_time)
            rsi = self.collection.get_value(self.symbol, closest_time, ValueType.RSI)
            if (quantity > 0.0) and (rsi >= self.upper):
                order = MarketOrder(self.symbol, OrderSide.SELL, quantity, current_time)
                order.message = "rsi ({:0.1f}) crossed above {:0.1f}".format(rsi, self.upper)
                self.portfolio.open_order(order)
            elif (cash > 0.0) and (rsi <= self.lower):
                order = MarketOrder(self.symbol, OrderSide.BUY, cash, current_time)
                order.message = "rsi ({:0.1f}) crossed below {:0.1f}".format(rsi, self.lower)
                self.portfolio.open_order(order)
