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
from datetime import datetime
from typing import Optional, List, Dict, Set

import pandas

from main.adapters.adapter import Adapter, AssetType, get_common_start_time, get_common_end_time, get_end_time, \
    get_start_time, get_column
from main.adapters.value_type import ValueType


class NotExactlyOneAdapterException(RuntimeError):
    pass


class AdapterCollection:
    adapters: List[Adapter]
    group_adapters: bool
    asset_type_overrides: Dict[str, AssetType]
    cache_key_date_override: Optional[datetime]

    def __init__(self):
        self.adapters = []
        self.group_adapters = True
        self.asset_type_overrides = {
            'ETH': AssetType.DIGITAL_CURRENCY,
            'LTC': AssetType.DIGITAL_CURRENCY
        }
        self.cache_key_date_override = None

    def retrieve_all_data(self):
        if self.cache_key_date_override is not None:
            self.set_all_cache_key_dates(self.cache_key_date_override)
        for adapter in self.adapters:
            adapter.add_all_columns()
            # adapter.calculate_asset_type()  add columns already does this... perhaps there were some that didn't?

    def set_all_cache_key_dates(self, cache_key_date: datetime) -> None:
        for adapter in self.adapters:
            adapter.cache_key_date = cache_key_date

    def get_all_cache_key_dates(self) -> Set[datetime]:
        return set([adapter.cache_key_date for adapter in self.adapters])

    # def add_arg(self, argument: Argument):
    #     for adapter in self.adapters:
    #         adapter.add_arg(argument)

    def get_adapters_with_value_type(self, value_type: ValueType) -> List[Adapter]:
        return [adapter for adapter in self.adapters if value_type in adapter.get_value_types]

    def get_adapters(self, symbol: str, value_type: ValueType) -> List[Adapter]:
        adapters_with_type: List[Adapter] = self.get_adapters_with_value_type(value_type)
        adapters_with_symbol: List[Adapter] = [adapter for adapter in adapters_with_type if adapter.symbol == symbol]
        assert len(adapters_with_symbol) <= 1, "Found {} adapters for symbol {} with value type {}, up to one is " \
                                               "expected.".format(len(adapters_with_symbol), symbol, value_type)
        # we don't support more than one adapter per symbol per value type - it would be ambiguous where to get data
        return adapters_with_symbol

    def get_adapter_or_none(self, symbol: str, value_type: ValueType) -> Optional[Adapter]:
        adapters: List[Adapter] = self.get_adapters(symbol, value_type)
        return adapters[0] if len(adapters) == 1 else None

    def get_adapter(self, symbol: str, value_type: ValueType) -> Adapter:
        """
        Return the adapter for the provided symbol and value type.
        :raise NotExactlyOneAdapterException if no matching adapters are found
        :param symbol: The symbol to get the adapter for
        :param value_type: The value type to get the adapter for
        :return: The adapter
        """
        adapters: List[Adapter] = self.get_adapters(symbol, value_type)
        if len(adapters) != 1:
            raise NotExactlyOneAdapterException("Found {} adapters for symbol {} with value type {}, exactly one is " \
                                                "expected.".format(len(adapters), symbol, value_type))
        return adapters[0]

    def has_value(self, symbol: str, instance: datetime, value_type: ValueType) -> bool:
        adapter: Adapter = self.get_adapter(symbol, value_type)
        exists = instance in adapter.data.index
        return exists

    def get_value(self, symbol: str, instance: datetime, value_type: ValueType) -> float:
        # Profiler.get_instance().enable()
        # price: float = self.get_value_closest_before_else_after(symbol, instance, value_type)
        adapter: Adapter = self.get_adapter(symbol, value_type)
        price = adapter.get_value(instance, value_type)  # it's an error condition if the times don't match.. callers
        # Profiler.get_instance().disable()
        return price

    def get_value_closest_before_else_after(self, symbol: str, instance: datetime, value_type: ValueType) -> float:
        adapter: Adapter = self
        # if adapter.has_time(instance):
        #     price = adapter.get_value(instance, value_type)
        # else:
        last: datetime = adapter.find_closest_before_else_after(adapter.data, instance)
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
        adapter: Adapter = self.get_adapter(symbol, value_type)
        all_items = adapter.get_column_on_or_before(before, value_type)
        return all_items.to_frame()

    def get_all_items_on_or_after(self, symbol, after: datetime, value_type: ValueType) -> pandas.DataFrame:
        adapter: Adapter = self.get_adapter(symbol, value_type)
        all_items = adapter.get_column_on_or_after(after, value_type)
        return all_items.to_frame()

    def get_all_items_between(self, symbol, after: datetime, before: datetime, value_type: ValueType) -> pandas.Series:
        adapter: Adapter = self.get_adapter(symbol, value_type)
        all_items = adapter.get_column_between(after, before, value_type)
        return all_items

    def add(self, to_add: Adapter) -> None:
        self.adapters.append(to_add)

    def get_columns(self, symbol: str, value_types: List[ValueType]) -> pandas.DataFrame:
        all_items = None
        for value_type in value_types:
            adapter: Adapter = self.get_adapter(symbol, value_type)
            if all_items is None:
                all_items = get_column(adapter.data, value_type).to_frame()
            else:
                all_items = all_items.join(get_column(adapter.data, value_type))
        return all_items

    def get_column(self, symbol: str, value_type: ValueType) -> pandas.Series:
        adapter: Adapter = self.get_adapter(symbol, value_type)
        all_items = get_column(adapter.data, value_type)
        return all_items

    def get_all_values(self, symbol: str, value_type: ValueType) -> pandas.Series:
        adapter: Adapter = self.get_adapter(symbol, value_type)
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
        adapter: Adapter = self.get_adapter(symbol, value_type)
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
        adapter: Adapter = self.get_adapter(symbol, value_type)
        return get_end_time(adapter.data)

    def get_all_times(self, before: Optional[datetime] = None) -> List[datetime]:
        times: List[datetime] = []
        for adapter in self.adapters:
            times += adapter.get_all_times(adapter.data)
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
