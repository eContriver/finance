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

from main.portfolio.order import StopOrder, OrderSide
from main.portfolio.portfolio import Portfolio
from main.strategies.singleSymbolStrategy import SingleSymbolStrategy


class BuyUpSellDownTrailing(SingleSymbolStrategy):
    buy_up: float
    sell_down: float

    def __init__(self, symbol: str, portfolio: Portfolio, buy_up: float, sell_down: float):
        super().__init__("Buy up {} Sell down {} Trailing".format(buy_up, sell_down), symbol, portfolio)
        self.buy_up = buy_up
        self.sell_down = sell_down
        self.build_price_collection(cache_key_date=None, start_time=portfolio.start_time, end_time=portfolio.end_time)

    def next_step(self, current_time: datetime,
                  order_filter: List[OrderSide] = (OrderSide.SELL, OrderSide.BUY)) -> None:
        last_time = self.portfolio.get_last_completed_time()
        cash = self.portfolio.quantities[self.collection.get_base_symbol()]
        quantity: float = self.portfolio.quantities[self.symbol]
        if (cash > 0.0) and OrderSide.BUY in order_filter:
            self.open_buy(current_time, last_time, cash)
        elif (quantity > 0.0) and OrderSide.SELL in order_filter:
            self.open_sell(current_time, last_time, quantity)

    def open_sell(self, current_time, last_time, quantity):
        last_order = self.portfolio.get_last_closed_order()
        assert last_order is None or last_order.order_side == OrderSide.BUY
        last_time = last_order.close_time if last_order is not None else last_time
        last_time = last_time if last_time is not None else current_time
        local_high = self.collection.find_local_high(self.symbol, current_time, last_time)
        # if local_high is None:
        #     local_high = self.collection.get_value(self.symbol, last_time, ValueType.HIGH)
        sell_price = self.sell_down * local_high
        if len(self.portfolio.open_orders) == 0:
            order = StopOrder(self.symbol, OrderSide.SELL, sell_price, quantity, current_time)
            order.message = "price crossed down {:0.2f} from high ({:0.2f} * {:0.2f})".format(
                sell_price, self.sell_down, local_high)
            self.portfolio.open_order(order)
        elif self.portfolio.open_orders[0].price < sell_price:
            self.portfolio.cancel_order(self.portfolio.open_orders[0], current_time)
            order = StopOrder(self.symbol, OrderSide.SELL, sell_price, quantity, current_time)
            order.message = "price crossed down {:0.2f} from high ({:0.2f} * {:0.2f})".format(
                sell_price, self.sell_down, local_high)
            self.portfolio.open_order(order)

    def open_buy(self, current_time, last_time, cash):
        last_order = self.portfolio.get_last_closed_order()
        assert last_order is None or last_order.order_side == OrderSide.SELL
        last_time = last_order.close_time if last_order is not None else last_time
        last_time = last_time if last_time is not None else current_time
        local_low = self.collection.find_local_low(self.symbol, current_time, last_time)
        # if local_low is None:
        #     local_low = self.collection.get_value(self.symbol, last_time, ValueType.LOW)
        buy_price = self.buy_up * local_low
        if len(self.portfolio.open_orders) == 0:
            order = StopOrder(self.symbol, OrderSide.BUY, buy_price, cash, current_time)
            order.message = "price crossed up {:0.2f} from low ({:0.2f} * {:0.2f})".format(
                buy_price, self.buy_up, local_low)
            self.portfolio.open_order(order)
        else:
            if self.portfolio.open_orders[0].price > buy_price:
                self.portfolio.cancel_order(self.portfolio.open_orders[0], current_time)
                order = StopOrder(self.symbol, OrderSide.BUY, buy_price, cash, current_time)
                order.message = "price crossed up {:0.2f} from low ({:0.2f} * {:0.2f})".format(
                    buy_price, self.buy_up, local_low)
                self.portfolio.open_order(order)

