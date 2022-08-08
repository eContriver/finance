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
from os import environ
from typing import Dict, List, Optional

from main.application.adapter import DataType, AssetType, Adapter, get_response_value_or_none, \
    IntervalNotSupportedException, insert_column, request_limit_with_timedelta_delay
from main.application.time_interval import TimeInterval
from main.application.value_type import ValueType
from main.application.converter import Converter
from main.application.argument import ArgumentKey
from main.common.locations import file_link_format


class UnknownAssetTypeException(RuntimeError):
    """
    When an asset type is requested which is not supported this exception is thrown.
    """
    pass


class Bitcoin(Adapter):
    name: str = 'bitcoin'
    url: str = 'http://127.0.0.1:18332'

    def __init__(self, symbol: str, asset_type: Optional[AssetType] = None):
        # api_user = 'sooth'
        if environ.get('BITCOIN_RPC_USER') is None:
            raise RuntimeError("The BITCOIN_RPC_USER environment variable is not set - this needs to be set to the RPC user")
        api_user = environ.get('BITCOIN_RPC_USER')
        # api_key = 'my_veruy_super_secret_and_super_long_password_nody_can_guess'
        if environ.get('BITCOIN_RPC_PASSWORD') is None:
            raise RuntimeError("The BITCOIN_RPC_PASSWORD environment variable is not set - this needs to be set to the RPC password")
        api_key = environ.get('BITCOIN_RPC_PASSWORD')
        super().__init__(symbol, asset_type)
        self.api_user = api_user
        self.api_key = api_key
        time = datetime.now()
        self.shared_index = datetime(year=time.year, month=time.month, day=time.day)
        self.converters: List[Converter] = [
            # we allow for multiple strings to be converted into the value type, first match is used
            Converter(ValueType.CONNECTION_COUNT, self.get_connection_count_response, []),
            Converter(ValueType.BALANCE, self.get_balance_response, ['balance']),
            Converter(ValueType.CHAIN_NAME, self.get_blockchain_info_response, ['chain']),
        ]

    def get_connection_count_response(self, value_type: ValueType) -> None:
        query = {
            "jsonrpc": "1.0",
            # "id": "curltest",
            "method": "getconnectioncount",
            "params": [],
        }
        raw_response, data_file = self.get_rpc_response(self.url, query, self.api_user, self.api_key, cache=False)
        self.validate_json_response(data_file, raw_response)
        self.translate(raw_response, value_type, 'result')

    def get_blockchain_info_response(self, value_type: ValueType) -> None:
        query = {
            "jsonrpc": "1.0",
            # "id": "curltest",
            "method": "getblockchaininfo",
            "params": [],
        }
        raw_response, data_file = self.get_rpc_response(self.url, query, self.api_user, self.api_key, cache=False)
        self.validate_json_response(data_file, raw_response)
        self.translate(raw_response, value_type, 'result')

    def get_balance_response(self, value_type: ValueType) -> None:
        # curl --user sooth --data-binary '{"jsonrpc": "1.0", "id": "curltest", "method": "getconnectioncount", "params": []}' -H 'content-type: text/plain;' http://127.0.0.1:18332/
        # Enter host password for user 'sooth':
        # {"result":10,"error":null,"id":"curltest"}
        query = {
            "jsonrpc": "1.0",
            # "id": "curltest",
            "method": "getbalance",
            "params": ["*", 6],
        }
        logging.debug("test")
        raw_response, data_file = self.get_rpc_response(self.url, query, self.api_user, self.api_key, cache=False)
        self.validate_json_response(data_file, raw_response)
        self.translate(raw_response, value_type, 'result')

    def translate(self, response_data, value_type: ValueType, key, data_date_format='%Y-%m-%d') -> None:
        """
        This method converts the raw data returned from rest API calls into
        :param response_data: Data from an API or URL request (raw data generally JSON, CSV, etc.)
        :param value_type: The value type we will be converting and the column we will be inserting
        :param key: The root key where we will pull the dictionary out of
        :param data_date_format: The incoming data time format, used to convert to datetime objects
        :return: None
        """
        if key not in response_data:
            raise RuntimeError("Failed to find key in data: {}".format(key))
        if not response_data[key]:
            raise RuntimeError(
                "There is no data (length is 0) for key: {} (maybe try a different time interval)".format(key))
        for converter in self.converters:
            if converter.value_type in self.data:
                continue  # if we've already added this value type, then don't do it again
            if converter.value_type != value_type:
                continue
            indexes = [self.shared_index]
            if value_type == ValueType.BALANCE:
                values = [response_data[key]]
            elif value_type == ValueType.CONNECTION_COUNT:
                values = [response_data[key]]
            elif value_type == ValueType.CHAIN_NAME:
                values = [response_data[key]["chain"]]
            # for entry_datetime, response_entry in response_data[key].items():
            #     value = None
            #     for response_key, response_value in response_entry.items():
            #         if response_key in converter.response_keys:
            #             value = float(response_value)
            #             break
            #     if value is None:  # we didn't find a match so move on to the next thing to convert
            #         continue
            #     # if converter.adjust_values:
            #     #     ratio = get_adjusted_ratio(response_entry)
            #     #     value = value * ratio
            #     indexes.append(datetime.fromisoformat(entry_datetime))
            #     values.append(value)
            insert_column(self.data, converter.value_type, indexes, values)


    @staticmethod
    def validate_json_response(data_file, raw_response, expects_result=True):
        if "error" in raw_response and raw_response["error"]:
            raise RuntimeError(
                "Error message in response - {}\n  See: {}".format(raw_response["error"],
                                                                   file_link_format(data_file)))
        if "warnings" in raw_response and raw_response["warnings"]:
            logging.warning(
                "Warning message in response - {}\n  See: {}".format(raw_response["warnings"],
                                                                   file_link_format(data_file)))
        if expects_result and "result" not in raw_response:
            raise RuntimeError("Failed to find the result in response: {}".format(file_link_format(data_file)))
        if expects_result and isinstance(raw_response["result"], dict) and "warnings" in raw_response["result"] and raw_response["result"]["warnings"]:
            logging.warning(
                "Warning messages in response - {}\n  See: {}".format(raw_response["result"]["warnings"],
                                                                     file_link_format(data_file)))

    # def delay_requests(self, data_file: Vstr) -> None:
    #     pass

    def get_is_digital_currency(self):
        return True

    def get_is_listed(self) -> bool:
        return not self.get_is_digital_currency()

    def get_is_physical_currency(self):
        return not self.get_is_digital_currency() and not self.get_is_listed()
