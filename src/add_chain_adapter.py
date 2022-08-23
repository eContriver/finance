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

import asyncio
from datetime import datetime, timedelta

from main.adapters.bitcoin import Bitcoin
from main.application.adapter import AssetType
from main.application.adapter_collection import AdapterCollection, set_all_cache_key_dates
from main.application.argument import ArgumentKey, Argument
from main.application.runner import print_copyright_notice, check_environment, configure_logging
from main.application.value_type import ValueType
from main.common.locations import get_and_clean_timestamp_dir, Locations


async def main():
    """
    This program can be used to add a chain adapter
    These are different from normal data adapters
    They normally represent a single Coin (Tokens are different) e.g. BTC or Bitcoin
    These adapters talk to that chain and can get Transactions and Block information
    This is not like price data with OHLC, volume, etc.

    Currently, the system does not know how to use this data, but we can look at how to integrate it
    For now we are just building these chain adapters so that we can talk to the chains directly

    Since this is the first time this has been added we are adding the adapter code directly
    Once we have this operational we should convert this to a ChainAdapter class and examine the
    commonalities with the current Adapter
    """
    locations = Locations()
    cache_dir = get_and_clean_timestamp_dir(locations.get_cache_dir('add_chain_adapter'))
    debug: bool = True
    configure_logging(cache_dir, debug)
    print_copyright_notice()
    check_environment()

    symbol: str = 'BTC'
    adapter_class = Bitcoin
    asset_type = AssetType.DIGITAL_CURRENCY

    end_time: datetime = datetime.now()
    # end_time = datetime(end_time.year, end_time.month, end_time.day)

    collection: AdapterCollection = AdapterCollection()
    adapter = adapter_class(symbol, asset_type)
    # adapter.base_symbol = base_symbol
    # adapter.asset_type = asset_type
    adapter.request_value_types = [  # The data to request from the adapter
        ValueType.CONNECTION_COUNT,
        ValueType.BALANCE,
        ValueType.CHAIN_NAME,
    ]  # NOTE: prints in this order, but reversed
    adapter.add_argument(Argument(ArgumentKey.WALLET_NAME, 'External'))
    adapter.add_argument(Argument(ArgumentKey.ADDRESS, 'bc1qudw9lsczpuknp2hfv3xyhpzvhc47a26zcr5wvf'))
    adapter.add_argument(Argument(ArgumentKey.SCAN_START, (datetime.now() - timedelta(weeks=8.0)).strftime("%s")))

    # adapter.add_argument(Argument(ArgumentKey.END_TIME, end_time))
    # adapter.add_argument(Argument(ArgumentKey.INTERVAL, price_interval))
    # adapter.cache_key_date = end_time
    # adapter.add_value_type(ValueType.BALANCE)
    collection.add(adapter)
    # Scanner/Explorer for Bitcoin testnet: https://www.blockchain.com/explorer?view=btc-testnet

    set_all_cache_key_dates(collection.adapters, end_time)
    collection.retrieve_all_data()

    # TODO: merge this into infra for ChainAdapter?
    # adapter.create_wallet()

    # TODO: skipping portfolio because we don't have pricing info, but we will need that for taxes...

    # asset_type = collection.asset_type_overrides[symbol] if symbol in collection.asset_type_overrides else None
    # value_types = [
    #     ValueType.BALANCE,
    # ]  # NOTE: this order does _not_ effect display
    # adapters: Dict[ValueType, Any] = {}
    # for value_type in value_types:
    #     adapters[value_type] = portfolio.get_adapter_class(value_type)

    print(adapter)
    print(adapter.data)

    # return True


if __name__ == "__main__":
    asyncio.run(main())
    # success = main()
    # exit(0 if success else -1)
