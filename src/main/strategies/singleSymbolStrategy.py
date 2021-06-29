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

from datetime import datetime, timedelta
from typing import Optional, List, Set, Any, Dict

from main.adapters.adapter import Adapter, AssetType
from main.adapters.valueType import ValueType
from main.adapters.adapterCollection import AdapterCollection
from main.adapters.argument import Argument, ArgumentType
from main.portfolio.portfolio import Portfolio
from main.strategies.strategy import Strategy


class SingleSymbolStrategy(Strategy):
    symbol: Optional[str]

    def __init__(self, title: str, symbol: str, portfolio: Portfolio):
        super().__init__(title, portfolio)
        self.symbol = symbol

    def __str__(self):
        string = self.symbol + " " + self.title
        string += "" if self.portfolio.start_time is None else " starting {}".format(self.portfolio.start_time)
        string += "" if self.portfolio.end_time is None else " ending {}".format(self.portfolio.end_time)
        return string

    def build_price_collection(self, cache_key_date: Optional[datetime] = None):
        asset_type = self.collection.asset_type_overrides[self.symbol] if self.symbol in \
                                                                          self.collection.asset_type_overrides else None
        value_types = [ValueType.OPEN, ValueType.HIGH, ValueType.LOW, ValueType.CLOSE]
        adapters: Dict[ValueType, Any] = {}
        for value_type in value_types:
            adapters[value_type] = self.portfolio.get_adapter_class(value_type)
        for value_type, adapter_class in adapters.items():
            adapter: Adapter = self.get_adapter(adapter_class, value_type, asset_type, cache_key_date)
            adapter.arguments.append(Argument(ArgumentType.INTERVAL, self.portfolio.interval))
            adapter.arguments.append(Argument(ArgumentType.START_TIME, self.portfolio.start_time))
            adapter.arguments.append(Argument(ArgumentType.END_TIME, self.portfolio.end_time))
            adapter.add_value_type(value_type)

    def get_adapter(self, adapter_class, value_type: ValueType, asset_type: AssetType,
                    cache_key_date: Optional[datetime] = None) -> Adapter:
        matching_adapters = [adapter for adapter in self.collection.adapters if (adapter.symbol == self.symbol) and
                             # this logic groups the adapters so there is only one per adapter_type
                             # if multiple adapters are needed, then set group_adapters to false
                             # TODO: Consider if group_adapters should belong to the strategy class, or move to collection
                             (not self.collection.group_adapters or (adapter_class == type(adapter)))]
                            # value_type in adapter.value_types] #
        if len(matching_adapters) == 1:
            adapter: Adapter = matching_adapters[0]
            # adapter.add_value_type(value_type)
        elif len(matching_adapters) == 0:
            adapter: Adapter = adapter_class(self.symbol, asset_type)
            # adapter.add_value_type(value_type)
            if cache_key_date is not None:
                adapter.cache_key_date = cache_key_date
            self.collection.adapters.append(adapter)
        else:
            raise RuntimeError("Only one adapter is allowed to be defined given a symbol and a value type. For symbol "
                               "{} found {} adapters that support value type {}: {}".format(self.symbol,
                                                                                            len(matching_adapters),
                                                                                            value_type,
                                                                                            matching_adapters))
        return adapter

    def build_macd_collection(self, slow, fast, signal, cache_key_date: Optional[datetime] = None):
        asset_type = self.collection.asset_type_overrides[self.symbol] if self.symbol in \
                                                                          self.collection.asset_type_overrides else None
        value_types = [ValueType.MACD, ValueType.MACD_HIST, ValueType.MACD_SIGNAL]
        adapters: Dict[ValueType, Any] = {}
        for value_type in value_types:
            adapters[value_type] = self.portfolio.get_adapter_class(value_type)
        for value_type, adapter_class in adapters.items():
            adapter: Adapter = self.get_adapter(adapter_class, value_type, asset_type, cache_key_date)
            adapter.arguments.append(Argument(ArgumentType.INTERVAL, self.portfolio.interval))
            adapter.arguments.append(Argument(ArgumentType.START_TIME, self.portfolio.start_time))
            adapter.arguments.append(Argument(ArgumentType.END_TIME, self.portfolio.end_time))
            adapter.arguments.append(Argument(ArgumentType.MACD_SLOW, slow))
            adapter.arguments.append(Argument(ArgumentType.MACD_FAST, fast))
            adapter.arguments.append(Argument(ArgumentType.MACD_SIGNAL, signal))
            adapter.add_value_type(value_type)
            # self.collection.adapters.append(adapter)

    def build_rsi_collection(self, period, cache_key_date: Optional[datetime] = None):
        asset_type = self.collection.asset_type_overrides[self.symbol] if self.symbol in \
                                                                          self.collection.asset_type_overrides else None
        value_types = [ValueType.RSI]
        adapters: Dict[ValueType, Any] = {}
        for value_type in value_types:
            adapters[value_type] = self.portfolio.get_adapter_class(value_type)
        for value_type, adapter_class in adapters.items():
            adapter: Adapter = self.get_adapter(adapter_class, value_type, asset_type, cache_key_date)
            # adapter: Adapter = data_adpter_class(self.symbol, asset_type)
            # if cache_key_date is not None:
            #     adapter.cache_key_date = cache_key_date
            adapter.arguments.append(Argument(ArgumentType.INTERVAL, self.portfolio.interval))
            adapter.arguments.append(Argument(ArgumentType.START_TIME, self.portfolio.start_time))
            adapter.arguments.append(Argument(ArgumentType.END_TIME, self.portfolio.end_time))
            adapter.arguments.append(Argument(ArgumentType.RSI_PERIOD, period))
            adapter.add_value_type(value_type)
            # self.collection.adapters.append(adapter)

    def build_book_collection(self, period, cache_key_date: Optional[datetime] = None):
        asset_type = self.collection.asset_type_overrides[self.symbol] if self.symbol in \
                                                                          self.collection.asset_type_overrides else None
        value_types = [ValueType.BOOK]
        adapters: Dict[ValueType, Any] = {}
        for value_type in value_types:
            adapters[value_type] = self.portfolio.get_adapter_class(value_type)
        for value_type, adapter_class in adapters.items():
            adapter: Adapter = adapter_class(self.symbol, asset_type)
            if cache_key_date is not None:
                adapter.cache_key_date = cache_key_date
            adapter.arguments.append(Argument(ArgumentType.INTERVAL, self.portfolio.interval))
            adapter.arguments.append(Argument(ArgumentType.START_TIME, self.portfolio.start_time))
            adapter.arguments.append(Argument(ArgumentType.END_TIME, self.portfolio.end_time))
            adapter.arguments.append(Argument(ArgumentType.BOOK, period))
            adapter.add_value_type(value_type)
            # self.collection.adapters.append(adapter)
