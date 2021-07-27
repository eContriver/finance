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


from datetime import datetime

from typing import List

from main.application.value_type import ValueType
from main.portfolio.order import OrderSide, MarketOrder
from main.portfolio.portfolio import Portfolio
from main.application.multi_symbol_strategy import MultiSymbolStrategy


class MultiDeltaSwap(MultiSymbolStrategy):
    delta: float
    last_symbol: str
    last_quantity: float

    def __init__(self, symbols: List[str], portfolio: Portfolio, delta: float):
        super().__init__("Delta swap {:0.2f}".format(delta), symbols, portfolio)
        self.delta = delta
        self.build_price_collection()
        self.last_symbol = symbols[1]
        self.last_quantity = self.portfolio.quantities[self.last_symbol]

    def next_step(self, current_time):
        last_time = self.portfolio.get_last_completed_time()
        last_time = current_time if last_time is None else last_time
        for symbol in self.symbols:
            quantity: float = self.portfolio.quantities[symbol]
            if quantity > 0.0:
                value_type: ValueType = ValueType.CLOSE
                price = self.collection.get_value(symbol, last_time, value_type)
                other_price = self.collection.get_value(self.last_symbol, last_time, value_type)
                swap_quantity = (price / other_price) * quantity
                if swap_quantity >= (self.delta * self.last_quantity):
                    self.open_sell(symbol, current_time, quantity, value_type)
                    self.open_buy(self.last_symbol, current_time, price * quantity, value_type)
                    self.last_symbol = symbol
                    self.last_quantity = quantity

    def open_sell(self, symbol: str, current_time: datetime, quantity: float, value_type: ValueType):
        order = MarketOrder(symbol, OrderSide.SELL, quantity, current_time, value_type)
        order.message = "swapping out {:0.2f} {}".format(quantity, symbol)
        self.portfolio.open_order(order)

    def open_buy(self, symbol: str, current_time: datetime, quantity: float, value_type: ValueType):
        order = MarketOrder(symbol, OrderSide.BUY, quantity, current_time, value_type)
        order.message = "swapping in {:0.2f} {}".format(quantity, symbol)
        self.portfolio.open_order(order)
