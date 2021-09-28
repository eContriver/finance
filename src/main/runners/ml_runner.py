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
import math
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Dict, List

import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.python.keras import Sequential
from tensorflow.python.keras.layers import LSTM, Dense

from main.adapters.alpha_vantage import AlphaVantage
from main.application.adapter import Adapter
from main.application.time_interval import TimeInterval
from main.application.value_type import ValueType
from main.common.time_zones import TimeZones
from main.application.adapter_collection import AdapterCollection
from main.application.runner import Runner, get_adapter_class, get_asset_type_overrides
from main.application.configurable_runner import NoSymbolsSpecifiedException


class MLReportType(Enum):
    LSTM = auto()


class MLRunner(Runner):
    def __init__(self):
        super().__init__()
        self.symbols = []
        self.adapter_class = None
        self.base_symbol = 'USD'
        self.price_interval = TimeInterval.DAY
        self.asset_type_overrides = {}
        self.report_types = []
        self.graph = False

    def get_config(self) -> Dict:
        asset_type_overrides = {}
        for symbol, asset_type in self.asset_type_overrides.items():
            asset_type_overrides[symbol] = asset_type.name
        config = {
            'adapter_class': self.adapter_class.__name__,
            'base_symbol': self.base_symbol,
            'symbols': self.symbols,
            'graph': self.graph,
            'price_interval': self.price_interval.value,
            'asset_type_overrides': asset_type_overrides,
            'report_types': [report_type.name for report_type in self.report_types],
        }
        return config

    def set_from_config(self, config, config_path):
        self.symbols = config['symbols']
        self.adapter_class = get_adapter_class(config['adapter_class'])
        report_types: List[str] = config['report_types']
        self.report_types = [MLReportType[report_type] for report_type in report_types]
        if 'asset_type_overrides' in config:
            self.asset_type_overrides = get_asset_type_overrides(config['asset_type_overrides'])
        if 'graph' in config:
            self.graph = config['graph']
        if 'base_symbol' in config:
            self.base_symbol = config['base_symbol']
        if 'price_interval' in config:
            self.price_interval = TimeInterval(config['price_interval'])
        self.check_member_variables(config_path)

    def check_member_variables(self, config_path: str):
        # validate_type('symbol', self.symbol, dict, config_path)
        if not self.symbols:
            raise NoSymbolsSpecifiedException(f"Please specify at least one symbol under 'symbol' in: "
                                              f"{config_path}")

    def get_run_name(self):
        return "MLRun"
        # return f"{self.price_interval.value.title()}_{self.adapter_class.__name__}"

