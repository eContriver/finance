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
from main.application.single_symbol_strategy import SingleSymbolStrategy


class LastBounce(SingleSymbolStrategy):
    """ uses a red to green on buy and a green to red to sell """
    ratio: float  # 2.0 ratio means the right side is at least double the left side
    threshold: float  # 0.01 means the last open close must be larger than a 1% difference to trigger

    def __init__(self, symbol: str, portfolio: Portfolio, ratio: float, threshold: float):
        super().__init__("Last bounce ratio {} threshold {}".format(ratio, threshold), symbol, portfolio)
        self.ratio = ratio
        self.threshold = threshold
        self.build_price_collection()

    def next_step(self, current_time: datetime,
                  order_filter: List[OrderSide] = (OrderSide.SELL, OrderSide.BUY)) -> None:
        cash: float = self.portfolio.quantities[self.collection.get_base_symbol()]
        quantity: float = self.portfolio.quantities[self.symbol]
        if (cash > 0.0) and OrderSide.BUY in order_filter:
            self.open_buy(current_time, cash)
        elif (quantity > 0.0) and OrderSide.SELL in order_filter:
            self.open_sell(current_time, quantity)

    def open_sell(self, current_time, quantity):
        times: List[datetime] = self.portfolio.get_completed_times()
        if len(times) < 2:
            return
        assert current_time == times[-1], "Unexpectedly failed while testing that the current time is the end of times"
        current_open = self.collection.get_value(self.symbol, times[-1], ValueType.OPEN)
        current_close = self.collection.get_value(self.symbol, times[-1], ValueType.CLOSE)
        previous_open = self.collection.get_value(self.symbol, times[-2], ValueType.OPEN)
        previous_close = self.collection.get_value(self.symbol, times[-2], ValueType.CLOSE)
        previous_closed_up = previous_close > previous_open
        current_closed_down = current_close < current_open
        one_close_is_lower = current_close < (previous_close * (1 - self.threshold))
        current_close_to_open = abs(current_close - current_open)
        previous_close_to_open = abs(previous_close - previous_open)
        ratio_met = previous_close_to_open * self.ratio < current_close_to_open
        if previous_closed_up and current_closed_down and one_close_is_lower and ratio_met:
            order = MarketOrder(self.symbol, OrderSide.SELL, quantity, current_time)
            order.message = "price bounced down from open={:0.3f};close={:0.3f} to open={:0.3f};close={:0.3f})".format(
                previous_open, previous_close, current_open, current_close)
            self.portfolio.open_order(order)

    def open_buy(self, current_time, cash):
        times: List[datetime] = self.portfolio.get_completed_times()
        if len(times) < 2:
            return
        assert current_time == times[-1], "Unexpectedly failed while testing that the current time is the end of times"
        current_open = self.collection.get_value(self.symbol, times[-1], ValueType.OPEN)
        current_close = self.collection.get_value(self.symbol, times[-1], ValueType.CLOSE)
        previous_open = self.collection.get_value(self.symbol, times[-2], ValueType.OPEN)
        previous_close = self.collection.get_value(self.symbol, times[-2], ValueType.CLOSE)
        previous_closed_down = previous_close < previous_open
        current_closed_up = current_close > current_open
        one_close_is_higher = current_close > (previous_close * (1 + self.threshold))
        current_close_to_open = abs(current_close - current_open)
        previous_close_to_open = abs(previous_close - previous_open)
        ratio_met = previous_close_to_open * self.ratio < current_close_to_open
        if previous_closed_down and current_closed_up and one_close_is_higher and ratio_met:
            order = MarketOrder(self.symbol, OrderSide.BUY, cash, current_time)
            order.message = "price bounced up from open={:0.3f};close={:0.3f} to open={:0.3f};close={:0.3f}".format(
                previous_open, previous_close, current_open, current_close)
            self.portfolio.open_order(order)
