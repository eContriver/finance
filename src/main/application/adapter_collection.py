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

#
#
#
import logging
from datetime import datetime
from typing import Optional, List, Dict, Set

import pandas

from main.application.adapter import Adapter, AssetType, get_common_start_time, get_common_end_time, get_end_time, \
    get_start_time, get_column, get_all_times, find_closest_before_else_after
from main.application.value_type import ValueType


class NotExactlyOneAdapterException(RuntimeError):
    """
    This exception is thrown when an adapter is requested and there isn't exactly one adapter matching.
    """
    pass


def filter_adapters(adapters: List[Adapter], symbol: str, value_type: ValueType) -> Adapter:
    """
    Return the adapter for the provided symbol and value type.
    :raise NotExactlyOneAdapterException if no matching adapters are found
    :param adapters: The list of adapters to filter
    :param symbol: The symbol to get the adapter for
    :param value_type: The value type to get the adapter for
    :return: The adapter matching the search criteria
    """
    adapters_with_type: List[Adapter] = [adapter for adapter in adapters if value_type in adapter.request_value_types]
    adapters_with_symbol: List[Adapter] = [adapter for adapter in adapters_with_type if adapter.symbol == symbol]
    if len(adapters_with_symbol) != 1:
        raise NotExactlyOneAdapterException("Found {} adapters for symbol {} with value type {}, exactly one is " \
                                            "expected.".format(len(adapters_with_symbol), symbol, value_type.name))
    return adapters_with_symbol[0]


def set_all_cache_key_dates(adapters: List[Adapter], cache_key_date: datetime) -> None:
    """
    Sets the cache key date on each of the provided adapters.
    :param adapters: A list of adapters to set the cache key dates on
    :param cache_key_date: The date to set the cache key date values to
    :return:
    """
    for adapter in adapters:
        adapter.cache_key_date = cache_key_date


def get_all_cache_key_dates(adapters) -> Set[datetime]:
    """
    Get unique list of all of the cache key dates from the list of adapters.
    :return:
    """
    return set([adapter.cache_key_date for adapter in adapters])


class AdapterCollection:
    """
    This class holds on to a collection (list) of adapters. The methods of this class facilitate clients asking for data
    from all of the adapters, so that clients don't have to keep track of what data lives in which adapter.

    A single adapter is capable of holding all different types of data in columns; However, where things breakdown is
    that sometimes a user wants Price (Open, Close, High, Low) to be on a Daily basis, and we want Earnings data on a
    Quarterly basis. For this case we use two adapters for the same symbol. Both adapters should be stored in an
    AdapterCollection, but each adapter would be using a different configuration.
    """
    adapters: List[Adapter]
    asset_type_overrides: Dict[str, AssetType]

    def __init__(self):
        self.adapters = []
        self.asset_type_overrides = {}

    def retrieve_all_data(self):
        """
        Retrieve the data for all of the columns (the requested value types set on the adapter) for each of the adapters
        :return:
        """
        for adapter in self.adapters:
            adapter.add_all_columns()

    def has_value(self, symbol: str, instance: datetime, value_type: ValueType) -> bool:
        adapter: Adapter = filter_adapters(self.adapters, symbol, value_type)
        exists = instance in adapter.data.index
        return exists

    def get_value(self, symbol: str, instance: datetime, value_type: ValueType) -> float:
        # Profiler.get_instance().enable()
        # price: float = self.get_value_closest_before_else_after(symbol, instance, value_type)
        adapter: Adapter = filter_adapters(self.adapters, symbol, value_type)
        price = adapter.get_value(instance, value_type)  # it's an error condition if the times don't match.. callers
        # Profiler.get_instance().disable()
        return price

    def get_value_closest_before_else_after(self, symbol: str, instance: datetime, value_type: ValueType) -> float:
        adapter: Adapter = filter_adapters(self.adapters, symbol, value_type)
        # if adapter.has_time(instance):
        #     price = adapter.get_value(instance, value_type)
        # else:
        last: datetime = find_closest_before_else_after(adapter.data, instance)
        price = adapter.get_value(last, value_type)
        return price

    def report(self, instance: datetime):
        report = ""
        for adapter in self.adapters:
            report += "{}:{}".format(adapter.symbol, adapter.get_row(instance).to_dict())
            # if adapter.symbol not in report:
            #     report[adapter.symbol] = ""
            # for value_type in adapter.value_types:
            #     value = self.get_value(adapter.symbol, instance, value_type)
            #     report[adapter.symbol] += "{}={:0.3f} ".format(value_type.value, value)
            #     # if value_type in adapter.data:
            #     #     value = self.get_value(adapter.symbol, instance, value_type)
            #     #     report[adapter.symbol] += "{}={:0.3f} ".format(value_type.value, value)
        logging.debug("On {} {}".format(instance, report))
        # logging.debug("On {} symbol {} {}".format(pandas.to_datetime(instance).tz_localize(TimeZones.get_tz()),
        #                                           adapter.symbol, report))

    def get_all_items_on_or_before(self, symbol: str, before: datetime, value_type: ValueType) -> pandas.DataFrame:
        adapter: Adapter = filter_adapters(self.adapters, symbol, value_type)
        all_items = adapter.get_column_on_or_before(before, value_type)
        return all_items.to_frame()

    def get_all_items_on_or_after(self, symbol, after: datetime, value_type: ValueType) -> pandas.DataFrame:
        adapter: Adapter = filter_adapters(self.adapters, symbol, value_type)
        all_items = adapter.get_column_on_or_after(after, value_type)
        return all_items.to_frame()

    def get_all_items_between(self, symbol, after: datetime, before: datetime, value_type: ValueType) -> pandas.Series:
        adapter: Adapter = filter_adapters(self.adapters, symbol, value_type)
        all_items = adapter.get_column_between(after, before, value_type)
        return all_items

    def add(self, to_add: Adapter) -> None:
        self.adapters.append(to_add)

    def get_columns(self, symbol: str, value_types: List[ValueType]) -> pandas.DataFrame:
        all_items = None
        for value_type in value_types:
            adapter: Adapter = filter_adapters(self.adapters, symbol, value_type)
            if all_items is None:
                all_items = get_column(adapter.data, value_type).to_frame()
            else:
                all_items = all_items.join(get_column(adapter.data, value_type))
        return all_items

    def get_column(self, symbol: str, value_type: ValueType) -> pandas.Series:
        adapter: Adapter = filter_adapters(self.adapters, symbol, value_type)
        all_items = get_column(adapter.data, value_type)
        return all_items

    def get_all_values(self, symbol: str, value_type: ValueType) -> pandas.Series:
        adapter: Adapter = filter_adapters(self.adapters, symbol, value_type)
        values = adapter.get_all_values(value_type)
        return values

    # Disabling: We aren't using it and it returns a row from one adapter. This could be
    # confusing for callers as for a given symbol we may have multiple adapters (different
    # ones for different value [data] types)
    # def get_row(self, symbol: str, instance: datetime, value_type: ValueType) -> pandas.Series:
    #     """
    #
    #     :param symbol:
    #     :param instance:
    #     :param value_type:
    #     :return:
    #     """
    #     adapter = self.get_adapter(symbol, value_type)
    #     return adapter.get_row(instance)

    def get_common_start_time(self) -> Optional[datetime]:
        start_times = []
        for adapter in self.adapters:
            start_times.append(get_common_start_time(adapter.data))
        return None if len(start_times) == 0 else max(start_times)

    def get_start_time(self, symbol: str, value_type: ValueType) -> Optional[datetime]:
        adapter: Adapter = filter_adapters(self.adapters, symbol, value_type)
        return get_start_time(adapter.data)

    def get_common_end_time(self) -> Optional[datetime]:
        end_times = []
        for adapter in self.adapters:
            end_times.append(get_common_end_time(adapter.data))
        return None if len(end_times) == 0 else min(end_times)

    def get_end_time(self, symbol: str, value_type: ValueType) -> Optional[datetime]:
        """
        Get the end time for a specific adapter from a collection
        :param symbol: The symbol of the adapter
        :param value_type: The value type of the adapter
        :return: The end time of the found adapter
        """
        adapter: Adapter = filter_adapters(self.adapters, symbol, value_type)
        return get_end_time(adapter.data)

    def get_all_times(self, before: Optional[datetime] = None) -> List[datetime]:
        times: List[datetime] = []
        for adapter in self.adapters:
            times += get_all_times(adapter.data)
        return sorted(list(set(times)))
        # times: List[datetime] = []
        # start_times = []
        # for adapter in self.adapters:
        #     this_times = adapter.get_all_times()
        #     if this_times:
        #         start_times.append(this_times[0])
        #         times += this_times
        # max_start_time = max(start_times)
        # trimmed_times = [instance for instance in times if instance >= max_start_time]
        # # Why filter these? It looks like we are getting rid of everything for a single data adapter that comes before
        # # the common data point. We could remove this and run the tests to see why, but apparently something makes an
        # # assumption that these times will all align. We may have already fixed this by moving Series, RSI, MACD, etc.
        # # to live in separate data adapters. They really support the concept of having a single data adapter with
        # # single storage to support all of these, but it becomes hard to initialize and allow different adapters for
        # # different types with this, so we just add a different adapter for each of the different types... thus this might not be needed anymore.
        # if before is not None:
        #     trimmed_times = [instance for instance in trimmed_times if instance < before]
        # return sorted(list(set(trimmed_times)))

    def get_base_symbol(self) -> str:
        base_symbol: str = ''
        for adapter in self.adapters:
            assert base_symbol == '' or base_symbol == adapter.base_symbol, "Found multiple base symbols {} and {}".format(
                base_symbol, adapter.base_symbol)
            base_symbol = adapter.base_symbol
        return base_symbol

    def get_symbols(self) -> List[str]:
        return list(set([adapter.symbol for adapter in self.adapters]))

    def find_local_high(self, symbol: str, current_time: datetime, start_time: datetime) -> float:
        items = self.get_all_items_between(symbol, start_time, current_time, ValueType.HIGH)
        local_high = items.max()
        return local_high

    def find_local_low(self, symbol: str, current_time: datetime, start_time: datetime) -> float:
        items = self.get_all_items_between(symbol, start_time, current_time, ValueType.LOW)
        local_low = items.min()
        return local_low
