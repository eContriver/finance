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
from typing import Optional, KeysView, List, Dict, Set

import pandas

from main.adapters.adapter import TimeInterval, AssetType
from main.adapters.value_type import ValueType
from datetime import datetime, timedelta

from main.adapters.adapter_collection import AdapterCollection
from main.common.profiler import Profiler
from main.portfolio.order import OrderSide, Order, LimitOrder


class Portfolio:
    title: str
    quantities: Dict[str, float]
    end_time: Optional[datetime]
    start_time: Optional[datetime]
    data: pandas.DataFrame
    indicator_data: Dict[str, pandas.DataFrame]
    canceled_orders: List[Order]
    closed_orders: List[Order]
    opened_orders: List[Order]
    open_orders: List[Order]
    remaining_times = List[datetime]
    report_collection: bool = False  # WARNING: fairly large run-time hit when this is enabled
    base_symbol: str
    interval: TimeInterval
    asset_type_overrides: Dict[str, AssetType]

    # data_adapter_classes: dict[ValueType, DataAdapter.__class__]

    def __init__(self, title: str, quantities: Dict[str, float],
                 start_time: Optional[datetime] = None, end_time: Optional[datetime] = None):
        self.title = title
        self.quantities = quantities
        self.end_time = end_time
        self.start_time = start_time
        self.data = pandas.DataFrame()
        self.indicator_data = {}
        self.canceled_orders = []
        self.closed_orders = []
        self.opened_orders = []
        self.open_orders = []
        self.remaining_times = []
        self.base_symbol = 'USD'
        self.interval = TimeInterval.DAY
        self.adapter_classes = {}
        self.asset_type_overrides = {
            'ETH': AssetType.DIGITAL_CURRENCY,
            'LTC': AssetType.DIGITAL_CURRENCY,
        }

    def __str__(self):
        as_str = "CAGR = {:8.2f} %".format(self.calculate_cagr() * 100.0)
        as_str += "  ROI = {:8.2f} %".format(self.calculate_roi() * 100.0)
        as_str += " " + self.get_positions()
        last_time = self.get_last_completed_time()
        # cash = [val for key, val in self.quantities.items() if key == self.base_symbol]
        # assert cash[0] == 0.0 or self.value_data[last_time] == round(cash[0], 2)
        # if last_time in self.value_data:
        #     as_str += "  Value = {:12.2f}".format(self.value_data[last_time])
        return as_str

    def get_current_value(self, instance: datetime, collection: AdapterCollection, value_type: ValueType):
        current_value: float = 0.0
        for symbol, quantity in self.quantities.items():
            if symbol == collection.get_base_symbol():
                current_value += quantity
            elif symbol in collection.get_symbols():
                current_value += quantity * collection.get_value(symbol, instance, ValueType.CLOSE)
        return current_value

    def get_current_value_of(self, symbol: str, instance: datetime, collection: AdapterCollection,
                             value_type: ValueType):
        current_value: float = 0.0
        if symbol == collection.get_base_symbol():
            current_value += self.quantities[symbol]
        elif symbol in collection.get_symbols():
            current_value += self.quantities[symbol] * collection.get_value(symbol, instance, ValueType.CLOSE)
        return current_value

    def get_tradable_quantity(self, symbol):
        held_for_trade: float = 0.0
        for order in self.open_orders:
            if (symbol == self.base_symbol or symbol == order.symbol) and order.order_side == OrderSide.SELL:
                held_for_trade += order.amount
            elif (symbol == self.base_symbol or symbol == order.symbol) and order.order_side == OrderSide.BUY:
                held_for_trade += order.amount
        return self.quantities[symbol] - held_for_trade

    def calculate_span(self) -> timedelta:
        start = self.start_time if self.start_time is not None else datetime.now() - timedelta(weeks=52 * 15)
        end = self.end_time if self.end_time is not None else datetime.now()
        span = end - start
        return span

    def get_positions(self) -> str:
        return " ".join(
            ' = '.join(("{:>5}".format(key), "{:10.2f}".format(val))) for (key, val) in self.quantities.items())

    def add_adapter_class(self, data_adapter_class, value_type: Optional[ValueType] = None):
        if value_type is None:  # then set it for every type
            for set_type in ValueType:
                self.adapter_classes[set_type] = data_adapter_class
        else:  # just set it for the specified type
            self.adapter_classes[value_type] = data_adapter_class

    def get_adapter_class(self, value_type: ValueType):
        return self.adapter_classes[value_type]

    def open_order(self, order: Order) -> None:
        """
        IMPORTANT: The aim is to let strategies open up orders, but they should not try to process them!
        By opening orders and calling next step we prevent a lot of mis-use of current-frame-of-reference knowledge.
        The caller (i.e. strategy designer) should find it difficult to access the infomration from the future, but
        find easy to use APIs when accessing current time or past times to make decisions about this time-frame.
        :param order: The order to open
        :return:
        """
        self.open_orders.append(order)
        self.opened_orders.append(order)
        order_message = "Opening {}.".format(str(order))
        portfolio = "Portfolio {}".format(str(self))
        logging.info("{:<205}{}".format(order_message, portfolio))

    def cancel_order(self, order: Order, instance: datetime):
        order.close_time = instance
        self.open_orders.remove(order)
        self.canceled_orders.append(order)
        order_message = "Canceling {}.".format(str(order))
        portfolio = "Portfolio {}".format(str(self))
        logging.info("{:<205}{}".format(order_message, portfolio))

    def close_order(self, base_symbol: str, order: Order, instance: datetime, collection: AdapterCollection):
        order.close_time = instance
        high: float = collection.get_value(order.symbol, instance, ValueType.HIGH)
        low: float = collection.get_value(order.symbol, instance, ValueType.LOW)
        open_price: float = collection.get_value(order.symbol, instance, ValueType.OPEN)
        close_price: float = collection.get_value(order.symbol, instance, ValueType.CLOSE)
        order.adjust_price_before_close(high, low, open_price, close_price)
        if order.order_side == OrderSide.BUY:
            total = order.amount / order.price  # amount in cash
            self.quantities[order.symbol] += total
            self.quantities[base_symbol] -= order.amount
        elif order.order_side == OrderSide.SELL:
            total = order.amount * order.price  # amount in shares/units
            self.quantities[base_symbol] += total
            self.quantities[order.symbol] -= order.amount
        else:
            raise RuntimeError("Unknown order side: {}".format(order.order_side))
        if order.price > high:
            raise RuntimeError(
                "Attempt to close order '{}' symbol '{}' with price above high '{}'.".format(order, order.symbol, high))
        elif order.price < low:
            raise RuntimeError(
                "Attempt to close order '{}' symbol '{}' with price below low '{}'.".format(order, order.symbol, low))
        if self.quantities[base_symbol] < 0.0:
            raise RuntimeError("After closing order '{}' symbol '{}' was left with a negative balance ({}), add some "
                               "way to protect against this in the strategy.".format(order, base_symbol,
                                                                                     self.quantities[base_symbol]))
        elif self.quantities[order.symbol] < 0.0:
            raise RuntimeError("After closing order '{}' symbol '{}' was left with a negative balance ({}), add some "
                               "way to protect against this in the strategy.".format(order, order.symbol,
                                                                                     self.quantities[order.symbol]))
        order_message = "Closing {} on {}.".format(str(order), instance)
        portfolio = "Portfolio {}  Value = {:12.2f}".format(str(self),
                                                            self.get_current_value(instance, collection,
                                                                                   ValueType.CLOSE))
        logging.info("{:<215} {:<1}".format(order_message, portfolio))
        self.open_orders.remove(order)
        self.closed_orders.append(order)

    def filter_dict_times(self, data: pandas.Series) -> pandas.Series:
        filtered = data[data.index >= self.start_time] if self.start_time is not None else data
        filtered = filtered[data.index <= self.end_time] if self.end_time is not None else filtered
        return filtered

    def filter_list_times(self, remaining_times):
        if self.start_time is not None and self.end_time is not None:
            remaining_times = [instance for instance in remaining_times if
                               (instance >= self.start_time) and (instance <= self.end_time)]
        elif self.start_time is not None:
            remaining_times = [instance for instance in remaining_times if (instance >= self.start_time)]
        elif self.end_time is not None:
            remaining_times = [instance for instance in remaining_times if (instance <= self.end_time)]
        return remaining_times

    def get_last_closed_order(self) -> Optional[Order]:
        last_closed_order: Optional[Order] = None
        for closed_order in self.closed_orders:
            if last_closed_order is None or (closed_order.close_time > last_closed_order.close_time):
                last_closed_order = closed_order
        return last_closed_order

    def get_last_completed_time(self) -> Optional[datetime]:  # this is effectively the current time - 1 index
        last_completed = self.get_completed_time_from_index(-1)
        return last_completed

    def get_first_completed_time(self) -> Optional[datetime]:
        last_completed = self.get_completed_time_from_index(0)
        return last_completed

    def get_completed_time_from_index(self, index: int) -> Optional[datetime]:
        time_from_index = None
        if len(self.data.index) > 0:
            times_completed = self.get_completed_times()
            time_from_index = times_completed[index]
        return time_from_index

    def get_completed_times(self) -> List[datetime]:
        times: List[datetime] = sorted(self.data.index)
        return times

    def set_remaining_times(self, collection: AdapterCollection) -> None:
        times: List[datetime] = collection.get_all_times()
        completed_times = self.data.index
        # completed_times: Set[datetime] = self.value_data.index
        remaining_times = set(times) - set(completed_times)  # asymmetric set difference
        remaining_times = self.filter_list_times(remaining_times)
        sorted_remaining = sorted(remaining_times)
        self.remaining_times = sorted_remaining

    def get_remaining_times(self) -> List[datetime]:
        return self.remaining_times

    def get_present_time(self, collection: AdapterCollection):
        remaining_times: List[datetime] = self.get_remaining_times()
        present_time = remaining_times[0]
        return present_time

    def run_to(self, collection: AdapterCollection, to_date: datetime):
        # Profiler.get_instance().enable()
        indexes = []
        # values = []
        for time in self.remaining_times:
            if time > to_date:
                continue
            if self.report_collection:
                collection.report(time)
            value = 0.0
            orders_to_close = []  # don't modify the open_orders while iterating...
            for order in self.open_orders:
                if order.is_satisfied(time, collection):
                    orders_to_close.append(order)
            for order in orders_to_close:
                self.close_order(collection.get_base_symbol(), order, time, collection)
            for symbol in collection.get_symbols():
                close_price: float = collection.get_value_closest_before_else_after(symbol, time, ValueType.CLOSE)
                # close_price: float = collection.get_value(symbol, time, ValueType.CLOSE)
                value += close_price * self.quantities[symbol]
            indexes.append(time)
            # values.append(value + self.quantities[collection.get_base_symbol()])
            self.data.loc[time, ValueType.CLOSE.value] = value + self.quantities[collection.get_base_symbol()]
        for time_to_remove in indexes:
            self.remaining_times.remove(time_to_remove)

    def summarize(self):
        logging.info('{:>18}:  {}'.format('Current positions', self.get_positions()))
        first_time = self.get_first_completed_time()
        initial_value = list(self.data.loc[first_time, :])[0]
        logging.info('{:>18}:  {:12.3f}  (time: {})'.format('Initial', initial_value, first_time))
        last_time = self.get_last_completed_time()
        final_value = list(self.data.loc[last_time, :])[0]
        logging.info('{:>18}:  {:12.3f}  (time: {})'.format('Total', final_value, last_time))
        roi = self.calculate_roi(first_time, last_time)
        opened = len(self.opened_orders)
        canceled = len(self.canceled_orders)
        closed = len(self.closed_orders)
        logging.info(
            '{:>18}:  {:10.3f} %  (orders opened:{}, canceled:{}, closed:{})'.format('ROI', roi * 100.0, opened,
                                                                                     canceled, closed))
        logging.info('{:>18}:  {:10.3f} %'.format('=> CAGR', self.calculate_cagr() * 100.0))

    def calculate_cagr(self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> float:
        last_time = end_time if end_time is not None else self.get_last_completed_time()
        first_time = start_time if start_time is not None else self.get_first_completed_time()
        interest_rate = 0.0
        if first_time is not None and last_time is not None:
            years = (last_time - first_time) / timedelta(weeks=52)
            roi = self.calculate_roi(first_time, last_time)
            interest_rate = self.calculate_rate(1.0, 1.0 + roi, years, 1)  # start 100%
        return interest_rate

    def calculate_roi(self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None):
        roi = 0.0
        if len(self.data.index) > 0:
            final_value = self.data.iloc[-1, 0]
            initial_value = self.data.iloc[0, 0]
            roi = (final_value / initial_value) - 1.0
        # last_time = end_time if end_time is not None else self.get_last_completed_time()
        # first_time = start_time if start_time is not None else self.get_first_completed_time()
        # if last_time is not None and first_time is not None:
        #     final_value = self.value_data[last_time]
        #     initial_value = self.value_data[first_time]
        #     roi = (final_value / initial_value) - 1.0
        return roi

    # APR = periodicRate * periodsInYear
    # APY = (1 + periodicRate) ** periodsInYear - 1
    # Default is CAGR, can set to periodsPerYear to 12 to see rate at compounding per month
    @staticmethod
    def calculate_rate(present_value, future_value, years, periods_per_year: int = 1):
        # FV = PV * (1 + r)**n    ==> r is rate_per_period (1.0 == 100%) and n is number_of_periods
        #  Check: 1104.71 = 1000.00 * (1 + (0.1 / 12)) ** 12
        # r = (FV / PV)**(1/n) - 1.0
        #  Check: 0.1 = (1104.71 / 1000.00)**(1/12) - 1.0
        #        rate = self.calculateRate(1000.0, 1104.71, 1.0)
        #        assert round(rate, 5) == 0.1
        yearly_rate = 0.0
        number_of_periods = float(years) * float(periods_per_year)
        if (present_value != 0.0) and (number_of_periods != 0.0):
            rate_per_period = (abs(float(future_value) / float(present_value))) ** (1.0 / number_of_periods) - 1.0
            yearly_rate = rate_per_period * periods_per_year  # rate_per_period = yearly_rate / periodsPerYear
        return yearly_rate  # if future_value >= present_value else -1.0 * yearly_rate
