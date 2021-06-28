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

from typing import Dict, List

from main.adapters.valueType import ValueType
from main.portfolio.order import StopOrder, OrderSide, MarketOrder
from main.portfolio.portfolio import Portfolio
from main.strategies.multiSymbolStrategy import MultiSymbolStrategy

"""
For each symbol divide the current_time SMA (@ period) by the SMA from look_back intervals.

This gives a relative factor if the SMA is tending up or down. A way of calculating price momentum.

Then we go through and compare all symbols 1 to 1 by dividing each relative factor by the other
and if this ratio of relative factors is greater than delta then we know that one symbol is
outpacing the other and if this is the case then we sell 100% of the under-performer and buy the other.
"""
class MultiRelativeSmaSwapDown(MultiSymbolStrategy):
    period: float
    delta: float
    look_back: int

    def __init__(self, symbols: List[str], portfolio: Portfolio, period: float, delta: float, look_back: int):
        super().__init__("SMA swap down {} looking back {} with period {}".format(delta, look_back, period), symbols, portfolio)
        self.period = period
        self.delta = delta
        self.look_back = look_back
        self.build_series_collection()
        self.build_sma_collection(self.period)

    def next_step(self, current_time: datetime) -> None:
        """
        :param current_time: this incremental steps time
        :return:
        """
        last_time = self.portfolio.get_last_completed_time()
        last_time = current_time if last_time is None else last_time
        relative_smas: Dict[str, float] = {}
        for symbol in self.symbols:
            sma = self.collection.get_value(symbol, last_time, ValueType.SMA)
            all_before = self.collection.get_symbol_handle(symbol).get_column_on_or_before(symbol, last_time,
                                                                                           ValueType.SMA)
            all_before = sorted(all_before)
            look_back_time = all_before[0] if len(all_before) < self.look_back else all_before[-self.look_back]
            look_back_sma = self.collection.get_value(symbol, look_back_time, ValueType.SMA)
            relative_smas[symbol] = sma / look_back_sma
            if symbol not in self.portfolio.indicator_data:
                self.portfolio.indicator_data[symbol] = {}
            self.portfolio.indicator_data[symbol][current_time] = relative_smas[symbol]
        cash: float = self.portfolio.quantities[self.portfolio.base_symbol]
        for relative_symbol, relative_sma in relative_smas.items():
            quantity: float = self.portfolio.quantities[relative_symbol]
            if quantity > 0.0 or cash > 0.0:
                for compare_symbol, compare_sma in relative_smas.items():
                    if compare_symbol == relative_symbol:
                        continue
                    ratio = relative_sma / compare_sma
                    if ratio <= self.delta:
                        value_type: ValueType = ValueType.OPEN
                        free_cash = self.portfolio.get_tradable_quantity(self.portfolio.base_symbol)
                        buying = cash if cash <= free_cash else free_cash
                        free_quantity = self.portfolio.get_tradable_quantity(relative_symbol)
                        selling = quantity if quantity <= free_quantity else free_quantity
                        if buying > 0:
                            self.open_buy(compare_symbol, current_time, buying, value_type)
                        elif selling > 0:
                            self.open_sell(relative_symbol, current_time, selling, value_type)
                            # Here we are setting up a sell for the future... tomorrow which would sell 100% of our symbol
                            # and then we have to calculate the purchase from that selling value price the next buying
                            # amount of cash available, however, the price will be different tomorrow, so we can either look
                            # into the future or just sell one day, and wait for the next day to purchase here we choose
                            # to do tha latter...
                            # price = self.collection.get_value(relative_symbol, current_time, value_type)
                            # cash_from_sale = price * quantity
                            # self.open_buy(compare_symbol, current_time, cash_from_sale, value_type)

    def open_sell(self, symbol: str, current_time: datetime, quantity: float, value_type: ValueType):
        order = MarketOrder(symbol, OrderSide.SELL, quantity, current_time, value_type)
        order.message = "swapping out {:0.2f} {}".format(quantity, symbol)
        self.portfolio.open_order(order)

    def open_buy(self, symbol: str, current_time: datetime, quantity: float, value_type: ValueType):
        order = MarketOrder(symbol, OrderSide.BUY, quantity, current_time, value_type)
        order.message = "swapping in {:0.2f} {}".format(quantity, symbol)
        self.portfolio.open_order(order)
