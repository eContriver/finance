# ------------------------------------------------------------------------------
#  Copyright 2021-2022 eContriver LLC
#  This file is part of Finance from eContriver.
#  -
#  Finance from eContriver is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  any later version.
#  -
#  Finance from eContriver is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  -
#  You should have received a copy of the GNU General Public License
#  along with Finance from eContriver.  If not, see <https://www.gnu.org/licenses/>.
# ------------------------------------------------------------------------------

import logging
from datetime import datetime
from typing import Dict, Any

from main.adapters.alpaca import Alpaca
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


def main():
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
    adapter_class = Alpaca
    # adapter_class = AlphaVantage
    price_interval = TimeInterval.DAY
    asset_type = AssetType.STOCK

    end_time: datetime = datetime.now()
    end_time = datetime(end_time.year, end_time.month, end_time.day)
    start_time: datetime = end_time - (1 * TimeInterval.YEAR.timedelta)

    collection: AdapterCollection = AdapterCollection()
    adapter = adapter_class(symbol, asset_type)
    adapter.base_symbol = base_symbol
    # adapter.asset_type = asset_type
    adapter.request_value_types = [
        ValueType.CLOSE,
        ValueType.LOW,
        ValueType.HIGH,
        ValueType.OPEN,

        ValueType.VOLUME,
    ]  # NOTE: prints in this order, but reversed (following OHLC here)
    adapter.add_argument(Argument(ArgumentKey.START_TIME, start_time))
    adapter.add_argument(Argument(ArgumentKey.END_TIME, end_time))
    adapter.add_argument(Argument(ArgumentKey.INTERVAL, price_interval))
    adapter.cache_key_date = end_time
    collection.add(adapter)

    set_all_cache_key_dates(collection.adapters, end_time)
    collection.retrieve_all_data()

    portfolio: Portfolio = Portfolio("Test", {'USD': 1000.0, symbol: 0.0}, start_time, end_time)
    portfolio.interval = price_interval
    # portfolio.interval = TimeInterval.WEEK
    portfolio.add_adapter_class(adapter_class)
    # portfolio.asset_type_overrides = asset_type_overrides
    portfolio.set_remaining_times(collection)

    # symbols: List[str] = ['NVDA']

    asset_type = collection.asset_type_overrides[symbol] if symbol in collection.asset_type_overrides else None
    value_types = [
        ValueType.OPEN,
        ValueType.HIGH,
        ValueType.LOW,
        ValueType.CLOSE,
        ValueType.VOLUME
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
    logging.info("-- Portfolio dump")
    print(portfolio.data)

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else -1)
