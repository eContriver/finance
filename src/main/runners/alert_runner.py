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
import sys
from datetime import datetime, timedelta
from typing import Dict, Optional, List

from main.adapters.adapter import TimeInterval, AssetType, Adapter
from main.adapters.value_type import ValueType
from main.adapters.argument import Argument, ArgumentType
from main.adapters.third_party_adapters.alpha_vantage import AlphaVantage
from main.adapters.third_party_adapters.yahoo import Yahoo
from main.adapters.adapter_collection import AdapterCollection, set_all_cache_key_dates
from main.common.locations import Locations
from main.common.report import Report
from main.runners.runner import Runner, validate_type, NoSymbolsSpecifiedException


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

        # GDP to Stimulus: 46% of GDP is stimulus?
        # Buffet indicator
        # Gold Silver Uranium

        # Short and or low available stocks...
        # Wendy's
        # Work horse
        # Archemodo
        # Go EV
        # Clover
        # FRX FSKR
        # Cheesecake factory

        # 'BYND',  # 'IMPM',  # Buy impossible at 120

        # Symbol, buy heavy, buy nibble,
        #  price within 5 years, 5 year return cagr, 5 year return under heavy cagr
        # self.close_boundaries = {
        #     'AAPL': [105.00, 120.00],
        #     # 200.00, 10.76 %, 13.75 %,
        #     'AMZN': [2700.00, 2800.00],
        #     #  5000.00, 12.30 %, 13.12 %,
        #     'GOOG': [2000.00, 2200.00],
        #     #  3000.00, 6.40 %, 8.45 %,
        #     'DIS': [150.00, 190.00],
        #     # 300.00, 9.57 %, 14.87 %,
        #     'PYPL': [260.00, 300.00],
        #     # 500.00, 10.76 %, 13.97 %,
        #     'TSLA': [600.00, 700.00],
        #     #  1750.00, 20.11 %, 23.87 %, 100
        #     'ETSY': [150.00, 200.00],
        #     # 'ETSY': [175.00, 200.00],
        #     # 500.00, 20.11 %, 23.36 %, 70
        #     'ENPH': [150.00, 170.00],
        #     # 'ENPH': [135.00, 170.00],
        #     # 400.00, 18.66 %, 24.26 %,
        #     'RDFN': [60.00, 70.00],
        #     # 200.00, 23.36 %, 27.23 %,
        #     'ABNB': [150.00, 170.00],
        #     #  (In Prog),, ,
        #     'PLTR': [22.00, 23.00],
        #     # 60.00, 21.14 %, 22.22 %,
        #     'EXPI': [30.00, 35.00],
        #     # 150.00, 33.78 %, 37.97 %,
        #     'SQ': [200.00, 220.00],
        #     # 380.00, 11.55 %, 13.70 %, 125
        #     'PINS': [60.00, 70.00],
        #     # 162.00, 18.27 %, 21.98 %,
        #     'W': [250.00, 265.00],
        #     # 625.00, 18.72 %, 20.11 %, 70
        #     'NIO': [34.00, 36.00],
        #     # 133.00, 29.87 %, 31.36 %, 100
        #     'CCIV': [17.00, 19.00],
        #     # 80.00, 33.31 %, 36.31 %,
        #     'LMND': [60.00, 80.00],
        #     # 'LMND': [70.00, 80.00],
        #     # 275.00, 28.01 %, 31.48 %,
        #     'PTON': [80.00, 100.00],
        #     # 290.00, 23.73 %, 29.38 %,
        #     'SFT': [7.25, 8.00],
        #     # 40.00, 37.97 %, 40.72 %, 40
        #     'GHVI': [11.50, 12.00],
        #     # 40.00, 27.23 %, 28.31 %,
        #     'API': [30.00, 40.00],
        #     # 110.00, 22.42 %, 29.67 %,
        #     # 'VYGVF': [16.00, 18.00],
        #     # 50.00, 22.67 %, 25.59 %,
        #     'RKT': [18.00, 20.00],
        #     # 30.00, 8.45 %, 10.76 %,
        #     'TTCF': [15.00, 17.00],
        #     # 30.00, 12.03 %, 14.87 %, 40
        #     # 'VRYYF': [4.50, 5.25],
        #     # 15.00, 23.36 %, 27.23 %,
        #     'BTC': [30000.00, 35000.00],
        #     #  105000.00, 19.00 %, 24.57 %,
        #     # 'ETH - USD': [2000.00, 2200.00],
        #     #  15000.00, 46.80 %, 49.63 %,
        #     # CASINO
        #     # BELOW, AKA
        #     # Lottery,, , , , 0.00 %, 0.00 %,
        #     # QS, 10,27.68,30.00,40.00,80.00, 14.87 %, 21.67 %,
        #     # NNDM, 10,6.31,, , , 0.00 %,,
        #     # MVIS, 10,15.19, Too
        #     # high
        #     # now,, , 0.00 %,,
        #     # GOEV, 10,7.55,9.00,11.00,30.00, 22.22 %, 27.23 %,
        #     'SOFI': [13.0, 15.0],
        # }

        # data_adapter_class = Yahoo
        collection: AdapterCollection = AdapterCollection()
        for symbol in self.close_boundaries.keys():
            asset_type: Optional[AssetType] = None  # means to auto select based off symbol
            adapter: Adapter = self.adapter_class(symbol, asset_type)
            adapter.base_symbol = 'USD'
            end_time = datetime.now()
            adapter.asset_type = self.asset_type_overrides[symbol] if symbol in self.asset_type_overrides else None
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
        asset_type_overrides: Dict[str, str] = config['asset_type_overrides']
        for symbol, asset_type in asset_type_overrides.items():
            self.asset_type_overrides[symbol] = AssetType[asset_type]
        self.close_boundaries = config['close_boundaries']
        class_name = config['adapter_class']
        self.adapter_class = getattr(
            sys.modules[f'main.adapters.third_party_adapters.{Report.camel_to_snake(class_name)}'], f'{class_name}')
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
