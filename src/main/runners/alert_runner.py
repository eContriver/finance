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
from datetime import datetime, timedelta
from typing import Dict, Optional, List

from main.application.adapter import TimeInterval, AssetType, Adapter
from main.application.value_type import ValueType
from main.application.argument import Argument, ArgumentType
from main.application.adapter_collection import AdapterCollection, set_all_cache_key_dates
from main.common.locations import Locations
from main.application.runner import Runner, validate_type, NoSymbolsSpecifiedException, get_adapter_class, \
    get_asset_type_overrides


class AlertRunner(Runner):
    close_boundaries: Dict[str, List[float]]
    adapter_class: Optional[type]
    base_symbol: str
    price_interval: TimeInterval
    asset_type_overrides: Dict[str, AssetType]

    def __init__(self):
        super().__init__()
        self.close_boundaries = {}
        self.adapter_class = None
        self.base_symbol = 'USD'
        self.price_interval = TimeInterval.DAY
        self.asset_type_overrides = {}

    # @staticmethod
    # def summarize(title, strategies: list[Strategy]):
    #     logging.info('== {}'.format(title))
    #     for strategy in strategies:
    #         logging.info({:>75}:  {}  ({} to {})".format(strategy.title
    #                                                       strategy.portfolio,
    #                                                       strategy.portfolio.start_time,
    #                                                       strategy.portfolio.end_time))

    def start(self, locations: Locations) -> bool:
        logging.info("#### Starting alert runner...")
        success = True
        collection: AdapterCollection = AdapterCollection()
        for symbol in self.close_boundaries.keys():
            asset_type: Optional[AssetType] = self.asset_type_overrides[symbol] if symbol in self.asset_type_overrides \
                else None
            # means to auto select based off symbol
            adapter: Adapter = self.adapter_class(symbol, asset_type)
            adapter.base_symbol = 'USD'
            end_time = datetime.now()
            adapter.asset_type = asset_type
            adapter.add_argument(Argument(ArgumentType.START_TIME, end_time - timedelta(days=1)))
            adapter.add_argument(Argument(ArgumentType.END_TIME, end_time))
            adapter.add_argument(Argument(ArgumentType.INTERVAL, self.price_interval))
            adapter.request_value_types = [ValueType.CLOSE]
            collection.add(adapter)
        set_all_cache_key_dates(collection.adapters, datetime.now())
        collection.retrieve_all_data()
        # collection.retrieve_data_parallel() # return values are not being passed

        heavy = []
        nibble = []
        wait = []

        for symbol, bounds in self.close_boundaries.items():
            collection.get_column(symbol, ValueType.CLOSE)
            # symbol_adapter: AdapterCollection = collection.get_symbol_handle(symbol)
            # end_time: datetime = symbol_adapter.get_end_time(symbol)
            # data: Dict[datetime, float] = symbol_adapter.get_all_items(symbol, ValueType.ADJUSTED_CLOSE)
            # price: float = data[end_time]
            # return price

            price: float = self.get_final_close(collection, symbol)
            heavy_price = bounds[0]
            nibble_price = bounds[1]
            if price < heavy_price:
                heavy.append(symbol)
            elif price <= nibble_price:
                nibble.append(symbol)
            else:
                wait.append(symbol)

        for symbol in wait:
            price: float = self.get_final_close(collection, symbol)
            heavy_price = self.close_boundaries[symbol][0]
            nibble_price = self.close_boundaries[symbol][1]
            logging.info("Wait on {} as it's price {} is above {} and nibble {}".format(symbol, price, heavy_price, nibble_price))

        for symbol in nibble:
            price: float = self.get_final_close(collection, symbol)
            heavy_price = self.close_boundaries[symbol][0]
            nibble_price = self.close_boundaries[symbol][1]
            logging.info("Buy nibble on {} as it's price {} is between {} and nibble {}".format(symbol, price, heavy_price, nibble_price))

        for symbol in heavy:
            price: float = self.get_final_close(collection, symbol)
            heavy_price = self.close_boundaries[symbol][0]
            nibble_price = self.close_boundaries[symbol][1]
            logging.info("Buy heavy on {} as it's price {} is below {} (nibble is: {})".format(symbol, price, heavy_price, nibble_price))

        return success

    def get_config(self) -> Dict:
        asset_type_overrides = {}
        for symbol, asset_type in self.asset_type_overrides.items():
            asset_type_overrides[symbol] = asset_type.name
        config = {
            'adapter_class': self.adapter_class.__name__,
            'base_symbol': self.base_symbol,
            'close_boundaries': self.close_boundaries,
            'price_interval': self.price_interval.value,
            'asset_type_overrides': asset_type_overrides,
        }
        return config

    def set_from_config(self, config, config_path):
        self.asset_type_overrides = get_asset_type_overrides(config['asset_type_overrides'])
        self.close_boundaries = config['close_boundaries']
        self.adapter_class = get_adapter_class(config['adapter_class'])
        self.base_symbol = config['base_symbol']
        self.price_interval = TimeInterval(config['price_interval'])
        self.check_member_variables(config_path)

    def check_member_variables(self, config_path: str):
        validate_type('close_boundaries', self.close_boundaries, dict, config_path)
        if not self.close_boundaries:
            raise NoSymbolsSpecifiedException(f"Please specify at least one symbol under 'close_boundaries' in: "
                                              f"{config_path}")

    def get_run_name(self):
        return f"{self.price_interval.value.title()}_{self.adapter_class.__name__}"

    @staticmethod
    def get_final_close(collection: AdapterCollection, symbol):
        end_time: datetime = collection.get_end_time(symbol, ValueType.CLOSE)
        # data: Dict[datetime, float] = symbol_adapter.get_column(symbol, ValueType.ADJUSTED_CLOSE)
        price: float = collection.get_value(symbol, end_time, ValueType.CLOSE)
        return price
