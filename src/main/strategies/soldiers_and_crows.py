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

from typing import List

from main.adapters.value_type import ValueType
from main.portfolio.order import MarketOrder, OrderSide
from main.portfolio.portfolio import Portfolio
from main.strategies.single_symbol_strategy import SingleSymbolStrategy


class SoldiersAndCrows(SingleSymbolStrategy):
    count: int

    def __init__(self, symbol: str, portfolio: Portfolio, count: int):
        super().__init__("{} white soldiers and black crows".format(count), symbol, portfolio)
        self.count = count
        self.build_price_collection()

    def next_step(self, current_time,
                  order_filter: List[OrderSide] = (OrderSide.SELL, OrderSide.BUY)) -> None:
        cash = self.portfolio.quantities[self.collection.get_base_symbol()]
        quantity: float = self.portfolio.quantities[self.symbol]
        if (cash > 0.0) and OrderSide.BUY in order_filter:
            self.buy(cash, current_time)
        elif (quantity > 0.0) and OrderSide.SELL in order_filter:
            self.sell(current_time, quantity)

    def sell(self, current_time, quantity):
        last_order = self.portfolio.get_last_closed_order()
        assert last_order is None or last_order.order_side == OrderSide.BUY
        last_time = last_order.close_time if last_order is not None else self.collection.get_common_start_time()
        opens = self.collection.get_all_items_on_or_after(self.symbol, last_time, ValueType.OPEN)
        closes = self.collection.get_all_items_on_or_after(self.symbol, last_time, ValueType.CLOSE)
        times = []
        for time in opens.index:
            if time > current_time:
                continue
            times.append(time)
        three_times = sorted(times)[-self.count:]
        do_it = True
        for time in three_times:
            if opens.loc[time, ValueType.OPEN] < closes.loc[time, ValueType.CLOSE]:
                do_it = False
                break
        if do_it and len(three_times) == self.count:
            order = MarketOrder(self.symbol, OrderSide.SELL, quantity, current_time)
            order.message = "three black crows closing"
            self.portfolio.open_order(order)

    def buy(self, cash, current_time):
        last_order = self.portfolio.get_last_closed_order()
        assert last_order is None or last_order.order_side == OrderSide.SELL
        last_time = last_order.close_time if last_order is not None else self.collection.get_common_start_time()
        opens = self.collection.get_all_items_on_or_after(self.symbol, last_time, ValueType.OPEN)
        closes = self.collection.get_all_items_on_or_after(self.symbol, last_time, ValueType.CLOSE)
        times = []
        for time in opens.index:
            if time > current_time:
                continue
            times.append(time)
        three_times = sorted(times)[-self.count:]
        do_it = True
        for time in three_times:
            if opens.loc[time, ValueType.OPEN] > closes.loc[time, ValueType.CLOSE]:
                do_it = False
                break
        if do_it and len(three_times) == self.count:
            order = MarketOrder(self.symbol, OrderSide.BUY, cash, current_time)
            order.message = "three white soldiers closing"
            self.portfolio.open_order(order)
