#!/usr/local/bin/python

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
from typing import List

from main.application.adapter import AssetType, Adapter
from main.application.time_interval import TimeInterval
from main.application.adapter_collection import AdapterCollection
from main.adapters.alpha_vantage import AlphaVantage
from main.application.value_type import ValueType


# @is_test
# @only_test
def new_adapter():
    """
    This test should not be enabled normally, but can be used to test a data adapter as it is added.
    We don't want this running regularly, because it would have to communicate with external sites every run.
    """
    base_symbol: str = 'USD'
    collection: AdapterCollection = AdapterCollection(base_symbol)
    symbols: List[str] = ['NVDA']
    asset_type: AssetType = AssetType.EQUITY
    # 1:
    query_type_types = [
        # QueryType.CASH_FLOW
        QueryType.BALANCE_SHEET
    ]
    # 2:
    value_types = [ValueType.ASSETS]
    # 3:
    interval = TimeInterval.QUARTER
    # 4:
    data_adapters = [
        # YahooAdapter,
        AlphaVantage
    ]
    for symbol in symbols:
        for data_adapter_ctor in data_adapters:
            data_adapter: Adapter = data_adapter_ctor(symbol, base_symbol)
            data_adapter.asset_type = asset_type
            symbol_handle: AdapterCollection = AdapterCollection(symbol)
            for query_type in query_type_types:  # QueryType:
                # 5: Add parameters
                data_adapter.balance_sheet_interval = interval
                symbol_handle.adapters[query_type] = data_adapter
            collection.add_symbol_handle(symbol_handle)

    collection.retrieve_all_data()

    for symbol in symbols:
        symbol_handle: AdapterCollection = collection.get_symbol_handle(symbol)
        end_time: datetime = symbol_handle.get_end_time(symbol)
        assert end_time is not None, "The end time is {} (None) we will stop testing now.".format(end_time)
        # if end_time is None:
        #     logging.warning("The end time is {} (None) we will skip reporting values.".format(end_time))
        #     break
        for value_type in value_types:
            value: float = symbol_handle.get_value(symbol, end_time, ValueType.CLOSE)
            logging.info("Value for {} is: {}".format(value_type, value))
        # assert close == 34.0, "close data is wrong - received: {}".format(close)

    return True


