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


from main.adapters.value_type import ValueType
from main.portfolio.order import MarketOrder, OrderSide
from main.portfolio.portfolio import Portfolio
from main.strategies.singleSymbolStrategy import SingleSymbolStrategy


class MacdCrossing(SingleSymbolStrategy):
    slow: float
    fast: float
    signal: float

    def __init__(self, symbol: str, portfolio: Portfolio, slow: float, fast: float, signal: float):
        super().__init__("MACD crossing slow {} fast {} signal {}".format(slow, fast, signal), symbol, portfolio)
        self.slow = slow
        self.fast = fast
        self.signal = signal
        self.build_price_collection(symbol)
        self.build_macd_collection(symbol, slow, fast, signal)

    def next_step(self, current_time):
        last_time = self.portfolio.get_last_completed_time()
        if last_time is not None:
            cash = self.portfolio.quantities[self.collection.get_base_symbol()]
            quantity: float = self.portfolio.quantities[self.symbol]
            hist = self.collection.get_value(self.symbol, last_time, ValueType.MACD_HIST)
            threshold = 0.0
            if (quantity > 0.0) and (hist <= threshold):
                order = MarketOrder(self.symbol, OrderSide.SELL, quantity, current_time)
                order.message = "macd histogram {:0.1f} crossed above {:0.1f}".format(hist, threshold)
                self.portfolio.open_order(order)
            elif (cash > 0.0) and (hist >= threshold):
                order = MarketOrder(self.symbol, OrderSide.BUY, cash, current_time)
                order.message = "macd histogram {:0.1f} crossed below {:0.1f}".format(hist, threshold)
                self.portfolio.open_order(order)
