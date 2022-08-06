#!python

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
from typing import Dict, Any

from main.adapters.alpaca import Alpaca
from main.adapters.alpha_vantage import AlphaVantage
from main.application.adapter import AssetType, Adapter
from main.application.adapter_collection import AdapterCollection, set_all_cache_key_dates
from main.application.argument import Argument, ArgumentKey
from main.application.runner import print_copyright_notice, check_environment, configure_logging
from main.application.strategy import MultipleMatchingAdaptersException
from main.application.time_interval import TimeInterval
from main.application.value_type import ValueType
from main.common.locations import get_and_clean_timestamp_dir, Locations
from main.portfolio.order import MarketOrder, OrderSide
from main.portfolio.portfolio import Portfolio


def next_step(portfolio: Portfolio, collection: AdapterCollection, symbol: str, current_time: datetime) -> None:
    cash = portfolio.quantities[collection.get_base_symbol()]
    if cash > 0.0:
        order = MarketOrder(symbol, OrderSide.BUY, cash, current_time)
        portfolio.open_order(order)


# def new_adapter(collection: AdapterCollection, adapter_class, base_symbol, symbol, asset_type) -> Adapter:
#     adapter = adapter_class(symbol, asset_type)
#     # adapter.base_symbol = base_symbol
#     # end_date = datetime.now()
#     # adapter.add_argument(Argument(ArgumentKey.START_TIME, end_date - 10 * TimeInterval.YEAR.timedelta))
#     # adapter.add_argument(Argument(ArgumentKey.END_TIME, end_date))
#     # adapter.cache_key_date = end_date
#     # adapter.asset_type = collection.asset_type_overrides[symbol] if symbol in collection.asset_type_overrides else None
#     return adapter
#

def add_adapter():
    """
    This program can be used to add a data adapter
    We don't want this running regularly, because it would have to communicate with external sites every run.
    """
    locations = Locations()
    cache_dir = get_and_clean_timestamp_dir(locations.get_cache_dir('add_adapter'))
    debug: bool = True
    configure_logging(cache_dir, debug)
    print_copyright_notice()
    check_environment()

    base_symbol: str = 'USD'
    symbol: str = 'NVDA'
    # adapter_class = Alpaca
    adapter_class = AlphaVantage
    price_interval = TimeInterval.WEEK
    asset_type = AssetType.EQUITY

    end_time: datetime = datetime.now()
    end_time = datetime(end_time.year, end_time.month, end_time.day)
    start_time: datetime = end_time - (1 * TimeInterval.YEAR.timedelta)

    collection: AdapterCollection = AdapterCollection()
    adapter = adapter_class(symbol, asset_type)
    adapter.base_symbol = base_symbol
    adapter.asset_type = asset_type
    adapter.request_value_types = [
        ValueType.CLOSE,
        ValueType.LOW,
        ValueType.HIGH,
        ValueType.OPEN,
    ] # NOTE: prints in this order, but reversed (following OHLC here)
    adapter.add_argument(Argument(ArgumentKey.START_TIME, start_time))
    adapter.add_argument(Argument(ArgumentKey.END_TIME, end_time))
    adapter.add_argument(Argument(ArgumentKey.INTERVAL, price_interval))
    adapter.cache_key_date = end_time
    collection.add(adapter)

    set_all_cache_key_dates(collection.adapters, end_time)
    collection.retrieve_all_data()

    portfolio: Portfolio = Portfolio("Test", {'USD': 1000.0, symbol: 0.0}, start_time, end_time)
    portfolio.interval = TimeInterval.WEEK
    portfolio.add_adapter_class(adapter_class)
    # portfolio.asset_type_overrides = asset_type_overrides
    portfolio.set_remaining_times(collection)

    # symbols: List[str] = ['NVDA']

    asset_type = collection.asset_type_overrides[symbol] if symbol in collection.asset_type_overrides else None
    value_types = [
        ValueType.OPEN,
        ValueType.HIGH,
        ValueType.LOW,
        ValueType.CLOSE
    ]  # NOTE: this order does _not_ effect display
    adapters: Dict[ValueType, Any] = {}
    for value_type in value_types:
        adapters[value_type] = portfolio.get_adapter_class(value_type)

    for value_type, adapter_class in adapters.items():
        group_adapters = True  # We can remove this, but leaving for now as we may want to make this configurable
        matching_adapters = [adapter for adapter in collection.adapters if (adapter.symbol == symbol) and
                             (not group_adapters or (adapter_class == type(adapter)))]
        if len(matching_adapters) == 1:
            adapter: Adapter = matching_adapters[0]
        elif len(matching_adapters) == 0:
            adapter: Adapter = adapter_class(symbol, asset_type)
            collection.adapters.append(adapter)
        else:
            raise MultipleMatchingAdaptersException("Only one adapter is allowed to be defined given a symbol and a "
                                                    "value type. For symbol {} found {} adapters that support value "
                                                    "type {}: {}".format(symbol,
                                                                         len(matching_adapters),
                                                                         value_type,
                                                                         matching_adapters))
        # adapter: Adapter = get_adapter(symbol, adapter_class, value_type, asset_type, cache_key_date)
        adapter.arguments.append(Argument(ArgumentKey.INTERVAL, portfolio.interval))
        adapter.arguments.append(Argument(ArgumentKey.START_TIME, portfolio.start_time))
        adapter.arguments.append(Argument(ArgumentKey.END_TIME, portfolio.end_time))
        adapter.add_value_type(value_type)

    print(adapter)
    print(adapter.data)

    logging.info("-- Example Buy And Hold")
    while True:
        remaining_times = portfolio.get_remaining_times()
        if not remaining_times:
            logging.info("No more dates left - ending")
            break
        current_time = remaining_times[0]
        portfolio.run_to(collection, current_time)
        next_step(portfolio, collection, symbol, current_time)
    portfolio.summarize()

    # asset_type: AssetType = AssetType.EQUITY
    # # 1:
    # # query_type_types = [
    # #     # QueryType.CASH_FLOW
    # #     QueryType.BALANCE_SHEET
    # # ]
    # # 2:
    # value_types = [ValueType.ASSETS]
    # # 3:
    # interval = TimeInterval.QUARTER
    # # 4:
    # data_adapters = [
    #     # YahooAdapter,
    #     AlphaVantage
    # ]
    # for symbol in symbols:
    #     for data_adapter_ctor in data_adapters:
    #         data_adapter: Adapter = data_adapter_ctor(symbol, base_symbol)
    #         data_adapter.asset_type = asset_type
    #         symbol_handle: AdapterCollection = AdapterCollection(symbol)
    #         for symbol_adapter in symbol_handle.adapters:
    #
    #         for query_type in query_type_types:  # QueryType:
    #             # 5: Add parameters
    #             data_adapter.balance_sheet_interval = interval
    #             symbol_handle.adapters[query_type] = data_adapter
    #         collection.add_symbol_handle(symbol_handle)
    #
    # collection.retrieve_all_data()
    #
    # for symbol in symbols:
    #     symbol_handle: AdapterCollection = collection.get_symbol_handle(symbol)
    #     end_time: datetime = symbol_handle.get_end_time(symbol)
    #     assert end_time is not None, "The end time is {} (None) we will stop testing now.".format(end_time)
    #     # if end_time is None:
    #     #     logging.warning("The end time is {} (None) we will skip reporting values.".format(end_time))
    #     #     break
    #     for value_type in value_types:
    #         value: float = symbol_handle.get_value(symbol, end_time, ValueType.CLOSE)
    #         logging.info("Value for {} is: {}".format(value_type, value))
    #     # assert close == 34.0, "close data is wrong - received: {}".format(close)

    return True


if __name__ == "__main__":
    success = add_adapter()
    exit(0 if success else -1)
