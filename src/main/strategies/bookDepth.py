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


from main.adapters.valueType import ValueType
from main.portfolio.order import MarketOrder, OrderSide
from main.portfolio.portfolio import Portfolio
from main.strategies.singleSymbolStrategy import SingleSymbolStrategy


class BookDepth(SingleSymbolStrategy):
    period: float

    def __init__(self, symbol: str, portfolio: Portfolio, period: float):
        super().__init__("Book depth period {:0.2f}".format(period), symbol, portfolio)
        self.period = period
        self.build_book_collection(self.period)

    def next_step(self, current_time):
        last_time = self.portfolio.get_last_completed_time()
        if last_time is not None:
            cash = self.portfolio.quantities[self.collection.base_symbol]
            quantity: float = self.portfolio.quantities[self.symbol]
            book = self.collection.get_value(self.symbol, last_time, ValueType.BOOK)
            if (quantity > 0.0) and (book >= self.upper):
                order = MarketOrder(self.symbol, OrderSide.SELL, quantity, current_time)
                order.message = "book ({:0.1f}) crossed above {:0.1f}".format(book, self.upper)
                self.portfolio.open_order(order)
            elif (cash > 0.0) and (book <= self.lower):
                order = MarketOrder(self.symbol, OrderSide.BUY, cash, current_time)
                order.message = "book ({:0.1f}) crossed below {:0.1f}".format(book, self.lower)
                self.portfolio.open_order(order)
