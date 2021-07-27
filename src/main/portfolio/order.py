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
from enum import Enum
from typing import Optional

import pandas

from main.application.adapter_collection import AdapterCollection
from main.common.time_zones import TimeZones
from main.application.value_type import ValueType


class OrderSide(Enum):
    BUY = 'buy'
    SELL = 'sell'


class Order:
    close_time: Optional[datetime]
    symbol: str
    order_side: OrderSide
    amount: float
    price: Optional[float]
    open_time: datetime
    prevent_execution_at_open: bool
    message: str
    enumeration: str

    def __init__(self, symbol: str, order_side: OrderSide, amount: float, open_time: datetime):
        self.symbol = symbol
        self.order_side = order_side
        self.amount = amount
        self.price = None
        self.open_time = open_time
        self.close_time = None
        self.message = ""
        self.enumeration = ""

    def __str__(self):
        if self.price is None:
            price = "market price"
            quantities = "{:0.4f} cash".format(self.get_cash_amount()) if self.order_side is OrderSide.BUY else \
                "{:0.4f} of".format(self.get_quantity_amount())
        else:
            price = "{:0.4f}".format(self.price)
            quantities = "{:0.4f} cash".format(self.get_cash_amount())
            quantities += " for {:0.4f}".format(self.get_quantity_amount())
        message = "" if not self.message else " execute if " + self.message
        return "{} {} {} {} at {} opened at {}{}".format(self.order_side, self.__class__.__name__, quantities,
                                                         self.symbol, price,
                                                         pandas.to_datetime(self.open_time).tz_localize(
                                                             TimeZones.get_tz()),
                                                         message)

    def get_quantity_amount(self):
        if self.order_side == OrderSide.BUY:
            quantity = self.amount / self.price if self.price is not None else None
        elif self.order_side == OrderSide.SELL:
            quantity = self.amount
        else:
            raise RuntimeError("Unknown order side: {}".format(self.order_side))
        return quantity

    def get_cash_amount(self):
        if self.order_side == OrderSide.BUY:
            cash = self.amount
        elif self.order_side == OrderSide.SELL:
            cash = self.amount * self.price
        else:
            raise RuntimeError("Unknown order side: {}".format(self.order_side))
        return cash

    def is_satisfied(self, instance: datetime, collection: AdapterCollection) -> bool:
        satisfied = False
        if self.order_side == OrderSide.SELL:
            satisfied = self.attempt_to_fill_sell(instance, collection)
        elif self.order_side == OrderSide.BUY:
            satisfied = self.attempt_to_fill_buy(instance, collection)
        return satisfied

    def attempt_to_fill_sell(self, time: datetime, collection: AdapterCollection) -> type(None):
        raise RuntimeError("Implement: {}".format(inspect.currentframe().f_code.co_name))

    def attempt_to_fill_buy(self, time: datetime, collection: AdapterCollection) -> type(None):
        raise RuntimeError("Implement: {}".format(inspect.currentframe().f_code.co_name))

    def place(self, data_adapter):
        raise RuntimeError("Implement: {}".format(inspect.currentframe().f_code.co_name))

    def adjust_price_before_close(self, high, low, open_price, close_price):
        raise RuntimeError("Implement: {}".format(inspect.currentframe().f_code.co_name))


class MarketOrder(Order):
    value_type: ValueType

    def __init__(self, symbol: str, order_side: OrderSide, amount: float, open_time: datetime,
                 value_type: ValueType = ValueType.OPEN):
        super().__init__(symbol, order_side, amount, open_time)
        self.enumeration = "m"
        self.value_type = value_type

    def attempt_to_fill_buy(self, time: datetime, collection: AdapterCollection):
        satisfied = True
        self.price = collection.get_value(self.symbol, time, ValueType.OPEN)
        return satisfied

    def attempt_to_fill_sell(self, time: datetime, collection: AdapterCollection):
        satisfied = True
        self.price = collection.get_value(self.symbol, time, ValueType.OPEN)
        return satisfied

    def place(self, data_adapter):
        data_adapter.place_market_order(self)

    def adjust_price_before_close(self, high, low, open_price, close_price):
        if high < self.price:
            logging.info("Adjusting close price from {:0.3f} to high {:0.3f} for: {}".format(self.price, high, self))
            self.price = high
        elif low > self.price:
            logging.info("Adjusting close price from {:0.3f} to low {:0.3f} for: {}".format(self.price, low, self))
            self.price = low


class LimitOrder(Order):
    def __init__(self, symbol: str, order_side: OrderSide, price: float, amount: float, open_time: datetime):
        super().__init__(symbol, order_side, amount, open_time)
        self.price = price
        self.enumeration = "l"

    def attempt_to_fill_buy(self, time: datetime, collection: AdapterCollection):
        low_price: float = collection.get_value(self.symbol, time, ValueType.LOW)
        satisfied = (low_price <= self.price)
        return satisfied

    def attempt_to_fill_sell(self, time: datetime, collection: AdapterCollection):
        high_price: float = collection.get_value(self.symbol, time, ValueType.HIGH)
        satisfied = (high_price >= self.price)
        return satisfied

    def place(self, data_adapter):
        if self.order_side == OrderSide.BUY:
            data_adapter.place_buy_limit_order(self.get_quantity_amount(), self.price)
        elif self.order_side == OrderSide.SELL:
            data_adapter.place_sell_limit_order(self.get_quantity_amount(), self.price)
        else:
            raise RuntimeError("Attempt to place order using unknown side (buy/sell): {}".format(self.order_side))

    def adjust_price_before_close(self, high, low, open_price, close_price):
        if high < self.price:
            if self.order_side == OrderSide.SELL:
                raise RuntimeError(
                    "Limit sell order attempted to close at price {:0.3f} but high was {:0.3f} for: {}".format(
                        self.price, high, self))
            elif self.order_side == OrderSide.BUY:
                logging.info(
                    "Adjusting limit buy order price from {:0.3f} to the high {:0.3f} for: {}".format(self.price, high,
                                                                                                      self))
                self.price = high
        elif low > self.price:
            if self.order_side == OrderSide.BUY:
                raise RuntimeError(
                    "Limit buy order attempted to close at price {:0.3f} but low was {:0.3f} for: {}".format(self.price,
                                                                                                             low, self))
            elif self.order_side == OrderSide.SELL:
                logging.info(
                    "Adjusting limit sell order price from {:0.3f} to the low {:0.3f} for: {}".format(self.price, low,
                                                                                                      self))
                self.price = low


class StopOrder(Order):
    def __init__(self, symbol: str, order_side: OrderSide, price: float, amount: float, open_time: datetime):
        super().__init__(symbol, order_side, amount, open_time)
        self.price = price
        self.enumeration = "t"

    def attempt_to_fill_buy(self, time: datetime, collection: AdapterCollection):
        high_price: float = collection.get_value(self.symbol, time, ValueType.HIGH)
        satisfied = (high_price >= self.price)
        return satisfied

    def attempt_to_fill_sell(self, time: datetime, collection: AdapterCollection):
        low_price: float = collection.get_value(self.symbol, time, ValueType.LOW)
        satisfied = (low_price <= self.price)
        return satisfied

    def place(self, data_adapter):
        if self.order_side == OrderSide.BUY:
            data_adapter.place_buy_stop_order(self.get_quantity_amount(), self.price)
        elif self.order_side == OrderSide.SELL:
            data_adapter.place_sell_stop_order(self.get_quantity_amount(), self.price)
        else:
            raise RuntimeError("Attempt to place order using unknown side (buy/sell): {}".format(self.order_side))

    def adjust_price_before_close(self, high, low, open_price, close_price):
        if high < self.price:
            logging.info("Adjusting close price from {:0.3f} to high {:0.3f} for: {}".format(self.price, high, self))
            self.price = high
        elif low > self.price:
            logging.info("Adjusting close price from {:0.3f} to low {:0.3f} for: {}".format(self.price, low, self))
            self.price = low
        # if the day opens at a price that would trigger the order, then it should execute at open price
        if self.order_side == OrderSide.BUY and open_price > self.price:
            logging.info(
                "Adjusting close price from {:0.3f} to open {:0.3f} for: {}".format(self.price, open_price, self))
            self.price = open_price
        elif self.order_side == OrderSide.SELL and open_price < self.price:
            logging.info(
                "Adjusting close price from {:0.3f} to open {:0.3f} for: {}".format(self.price, open_price, self))
            self.price = open_price
