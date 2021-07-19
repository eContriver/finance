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


import csv
import inspect
import json
import logging
import os.path
import shutil
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, List, Any
from urllib.parse import urlparse

import numpy
import pandas
import requests

from main.adapters.argument import Argument, ArgumentType
from main.adapters.converter import Converter
from main.adapters.value_type import ValueType
from main.common.locations import file_link_format


# class MissingCacheKeyException(RuntimeError):
#     pass


class DuplicateRawIndexesException(RuntimeError):
    """
    When data is added
    """
    pass


class AssetType(Enum):
    """
    The AssetType class is used to differentiate the different asset types. For instance if the symbol BTC is used, then
    we expect DIGITAL_CURRENCY, if USD is used we expect PHYSICAL_CURRENCY, and for the symbol AAPL it should be EQUITY.

    There are cases like ETH where it is ambiguous (it could be an EQUITY or a DIGITAL_CURRENCY).

    When an asset type is not specified (i.e. it is None), then the system will attempt to auto-calculate the value by
    looking up the symbol in lists provided to the adapters. In ambiguous cases there is generate an asset_type_override
    available where specific asset types can be set for different symbols.
    """
    EQUITY = 'equity'
    DIGITAL_CURRENCY = 'digital currency'
    PHYSICAL_CURRENCY = 'physical currency'


class DataType(Enum):
    """
    The DataType class is used to define the type of data that is returned from an API. This is used for both rest API
    calls and module API calls (i.e. which go into other libraries)
    """
    JSON = 1
    CSV = 2
    DATAFRAME = 3


class TimeInterval(Enum):
    """
    The TimeInterval enumeration is intended to represent the time intervals between data. It is generally used when
    querying an adapter for data as most APIs require an interval.

    The TimeInterval class is also used when saving and reading configuration information from configuration files.

    The string value can be used for messages, but it's purpose is for human readable files such as configuration files
    etc. The timedelta value is intended to be used for calculations and comparisons between the time intervals.

    Retrieve the values as:
      TimeValue.SEC15.value -> '15sec'
      TimeValue.SEC15.timedelta -> timedelta(seconds=15)
    """
    SEC15 = '15sec', timedelta(seconds=15)
    MIN1 = '1min', timedelta(minutes=1)
    MIN5 = '5min', timedelta(minutes=5)
    MIN10 = '10min', timedelta(minutes=10)
    MIN15 = '15min', timedelta(minutes=15)
    MIN30 = '30min', timedelta(minutes=30)
    HOUR = '60min', timedelta(hours=1)
    HOUR6 = '6hour', timedelta(hours=6)
    DAY = 'daily', timedelta(days=1)
    WEEK = 'weekly', timedelta(weeks=1)
    MONTH = 'monthly', timedelta(days=30)  # hmm?
    QUARTER = 'quarterly', timedelta(weeks=13)
    YEAR = 'yearly', timedelta(weeks=52)
    YEAR2 = '2year', timedelta(weeks=52 * 2)
    YEAR5 = '5year', timedelta(weeks=52 * 5)

    def __new__(cls, value, delta):
        member = object.__new__(cls)
        member._value_ = value
        member.timedelta = delta
        return member


def get_common_start_time(data: pandas.DataFrame) -> Optional[datetime]:
    """
    Collects the first valid (non nan/None) index (datetime) for each column and selects the max of those.
    D1  1    None
    D2  1    1     <- Returns D2 assuming sorted indices D1 is less than D2 in datetime (epoch)
    D3  1    1
    D4  None 1

    NOTE: This will also return a seemingly incorrect index when there is no overlap
    D1  1    None
    D2  1    None
    D3  None 1     <- Returns D3
    D4  None 1

    :param data: DataFrame with datetime index and one or more columns
    :return: The common start time across all columns with valid data
    """
    valid_start_times = []
    data = data.sort_index(ascending=True)
    for column in data:
        valid_start_times.append(data[column].first_valid_index())
    return None if len(valid_start_times) == 0 else max(valid_start_times)


def get_common_end_time(data: pandas.DataFrame) -> Optional[datetime]:
    """
    Collects the last valid (non nan/None) index (datetime) for each column and selects the max of those.
    D1  1    None
    D2  1    1
    D3  1    1     <- Returns D3 assuming sorted indices D1 is less than D2 in datetime (epoch)
    D4  None 1

    NOTE: This will also return a seemingly incorrect index when there is no overlap
    D1  1    None
    D2  1    None  <- Returns D2
    D3  None 1
    D4  None 1

    :param data: DataFrame with datetime index and one or more columns
    :return: The common start time across all columns with valid data
    """
    valid_end_times = []
    data = data.sort_index(ascending=True)
    for column in data:
        valid_end_times.append(data[column].last_valid_index())
    return None if len(valid_end_times) == 0 else min(valid_end_times)


def get_default_cache_key_date() -> datetime:
    """
    Get the default cache key date using a central function in case we decide to change this, it is in one place.
    :return: The current datetime
    """
    return datetime.now()


class Adapter:
    """
    Adapters are used to interface with 3rd party websites.

    The expectation is that a client can ask for any of the supported ValueTypes from the Adapter and it will figure out
    how to get that data and return a pandas DataFrame that has the index of datetimes with a column containing that
    data.

    This data retrieval is generally done using a REST API or a module API. The results are expected to be cached. This
    prevents clients from being charged for multiple calls to retrieve the same data.

    The data is generally cached using a high-level directory which has a date stamp and is normally available for a
    24-hour period. This means that every 24-hours new data will be requested even if the same API is called with the
    same inputs. Then the caches are determined using the arguments to retrieve data.

    There is an option to not use the cache for things that must be retrieved every time like order status or real-time
    data.
    """
    symbol: str
    asset_type = Optional[AssetType]
    base_symbol: str
    cache_key_date: Optional[datetime]
    cache_key_filter: List[str]
    content_cache = Dict[str, Any]
    arguments: List[Argument]
    data: pandas.DataFrame
    converters: List[Converter]
    value_types: List[ValueType]
    query_args: Dict[str, str]  # for things like macd_fast, macd_slow, macd_signal, etc.
    cache_root_dir: Optional[str]

    def add_extra_data(self, value_type, visualizer):
        pass

    def __init__(self, symbol: str, asset_type: Optional[AssetType] = None):
        self.symbol = symbol
        self.base_symbol = 'USD'
        self.cache_key_date = None
        self.cache_key_filter = ['apikey', 'token']
        self.content_cache = {}

        self.asset_type = asset_type
        self.arguments = []
        self.data = pandas.DataFrame()

        self.value_types = []
        self.query_args = {}

        script_dir = os.path.dirname(os.path.realpath(__file__))
        cache_dir = os.path.join(script_dir, '..', '..', '..', '.cache', self.__class__.__name__)
        self.cache_root_dir = os.path.realpath(cache_dir)

    def __str__(self):
        return f"{self.__class__.__name__} adapter with {self.symbol} ({self.base_symbol}) {self.asset_type} (cache " \
               f"key:{self.cache_key_date})"

    def add_value_type(self, value_type: ValueType):
        if value_type not in self.value_types:
            self.value_types.append(value_type)

    def add_all_columns(self):
        for value_type in self.value_types:
            self.add_column(value_type)

    def add_column(self, value_type: ValueType) -> None:
        if self.cache_key_date is None:
            self.cache_key_date = get_default_cache_key_date()
        # self.cache_key_date = datetime(year=2021, month=6, day=29)
            # raise MissingCacheKeyException("The cache key should be set on each Adapter or on the Collection so that "
            #                                "the default makes since for the adapter type, but should also allow the "
            #                                "user to pin a cache key date so that they can work without downloading "
            #                                "more data if they are working on a large dataset.")
        self.calculate_asset_type()  # we chose to delay the asset calculation, until we are already talking to the
        # server, can this just be set on the adapter, directly?
        converter = self.get_converter(value_type)
        # Consider passing the converter so the function gets it. Without this 3rd party adapters will write one
        # function per type, which might be a good thing, so perhaps we leave it? e.g.
        # converter.get_response_callback(converter)
        converter.get_response_callback(value_type)
        assert value_type in self.data, "Parsing response data failed, was adding column for value type '{}', but " \
                                        "no data was present after getting and parsing the response. Does the " \
                                        "converter have the correct keys/locations for the raw data?".format(value_type)

    def get_converter(self, value_type):
        converters = [converter for converter in self.converters if value_type == converter.value_type]
        assert len(converters) == 1, "Found {} converters for value type '{}', one and only one converter is " \
                                     "supported per value type: {}".format(len(converters), value_type, converters)
        converter = converters[0]
        return converter

    @staticmethod
    def merge(a, b, path=None):
        if path is None:
            path = []
        for key in b:
            if key in a:
                if isinstance(a[key], dict) and isinstance(b[key], dict):
                    Adapter.merge(a[key], b[key], path + [str(key)])
                elif a[key] == b[key]:
                    pass  # same leaf value
                else:
                    raise Exception('Multiple data sets contain the same key, conflict at %s' %
                                    '.'.join(path + [str(key)]))
            else:
                a[key] = b[key]
        return a

    def get_api_response(self, api, args, cache: bool = True, data_type: DataType = DataType.JSON):
        data_id = self.get_key_for_api_request(api, args)
        add_timestamp = not cache
        data_file, lock_dir = self.get_lock_dir_and_data_file(data_id, add_timestamp, data_type)
        acquired_lock = False
        try:
            acquired_lock = self.lock(data_file, lock_dir)
            if not os.path.exists(data_file):  # only download files once per data_id - includes cache_key (e.g.daily)
                self.delay_requests(data_file)
                self.write_api_response_to_file(data_file, api, args, data_type)
                logging.debug('Data saved to: {}'.format(file_link_format()))
            else:
                logging.debug('Using cached file: {}'.format(file_link_format()))
        except Exception:
            raise
        finally:
            if acquired_lock and os.path.exists(lock_dir):
                os.rmdir(lock_dir)
        data = self.read_cache_file(data_file, data_type, cache)
        self.validate_data(data)
        return data, data_file

    def get_indicator_key(self):
        self.calculate_asset_type()
        indicator_key = self.symbol
        if self.asset_type == AssetType.DIGITAL_CURRENCY:
            indicator_key = "{}-{}".format(self.symbol, self.base_symbol)  # e.g. BTC-USD
        return indicator_key

    def get_url_response(self, url, query, cache: bool = True, data_type: DataType = DataType.JSON, delay: bool = True):
        data_id = self.get_key_for_url_request(query, url)
        add_timestamp = not cache
        data_file, lock_dir = self.get_lock_dir_and_data_file(data_id, add_timestamp, data_type)
        acquired_lock = False
        try:
            acquired_lock = self.lock(data_file, lock_dir)
            if not os.path.exists(data_file):  # only download files once per data_id - includes cache_key (e.g.daily)
                if delay:
                    self.delay_requests(data_file)
                self.write_url_response_to_file(data_file, query, url)
                logging.debug('Data saved to: {}'.format(file_link_format(data_file)))
            else:
                logging.debug('Using cached file: {}'.format(file_link_format(data_file)))
        except Exception:
            raise
        finally:
            if acquired_lock and os.path.exists(lock_dir):
                os.rmdir(lock_dir)
        data = self.read_cache_file(data_file, data_type, cache)
        self.validate_data(data)
        return data, data_file

    @staticmethod
    def get_key_for_api_request(function, args):
        args_string = "" if len(args) == 0 else "." + "_".join(
            [str(arg).replace(':', '_').replace('/', '_').replace('.', '_') for arg in args.values()])
        cls = function.__self__.__class__.__name__ + "." if hasattr(function, '__self__') else ""
        key = '{}{}{}'.format(cls, function.__name__, args_string)
        return key

    def get_key_for_url_request(self, query, url):
        lower_values = []
        for key, value in query.items():
            if key not in self.cache_key_filter:
                lower_values.append(str(value).lower())
        name = '' if not lower_values else '_' + '_'.join(lower_values)
        path = urlparse(url).path
        path = path.strip('/').replace('/', '_')
        key = "{}{}".format(path, name)
        return key

    def read_cache_file(self, data_file, data_type, cache: bool = True):
        content_cache_key = "{}-{}".format(data_file, data_type)
        if cache and content_cache_key in self.content_cache:  # read files only once per process, else get from memory
            logging.debug('Using cached content for: {} (type: {})'.format(file_link_format(data_file),
                                                                           data_type))
            data = self.content_cache[content_cache_key]
        else:
            logging.debug('Reading data from cache file: {} (type: {})'.format(file_link_format(data_file),
                                                                               data_type))
            if data_type == DataType.JSON:
                with open(data_file, 'r') as fd:
                    data = json.load(fd)
            elif data_type == DataType.DATAFRAME:
                data = pandas.read_pickle(data_file)
            elif data_type == DataType.CSV:
                with open(data_file, 'r') as fd:
                    reader = csv.reader(fd, delimiter=',')
                    data = []
                    for row in reader:
                        data.append(row)
            else:
                raise RuntimeError("Unrecognized data type: {}".format(data_type))
            self.content_cache[content_cache_key] = data
        return data

    @staticmethod
    def write_api_response_to_file(data_file, api, args, data_type):
        logging.debug('Requesting data from: {}({})'.format(api, args))
        response = api(**args)
        logging.debug('Received response: {}'.format(response))
        if data_type == DataType.JSON:
            with open(data_file, 'w') as fd:
                json.dump(response, fd, indent=4)
        elif data_type == DataType.DATAFRAME:
            response.to_pickle(data_file)
        elif data_type == DataType.CSV:
            with open(data_file, 'w') as fd:
                fd.write(response)
        else:
            raise RuntimeError("Unrecognized data type: {}".format(data_type))

    @staticmethod
    def write_url_response_to_file(data_file, query, url):
        url_query = '' if not query else '?' + '&'.join(['%s=%s' % (key, value) for (key, value) in query.items()])
        url = '{}{}'.format(url, url_query)
        logging.debug('Requesting data from: {}'.format(url))
        response = requests.get(url)
        logging.debug('Received response: {}'.format(response))
        response.raise_for_status()
        with open(data_file, 'w') as fd:
            fd.write(response.text)

    def get_lock_dir_and_data_file(self, data_id, timestamp: bool, data_type: DataType):
        self.cache_root_dir = os.path.realpath(self.cache_root_dir)
        self.clean_cache_dirs()
        # only letting one query run at a time makes the file timestamps work, and doesn't hammer the servers
        lock_dir = self.get_single_query_lock_dir()
        # can be used to lock per request, but then race conditions exist with file timestamps
        #       see AlphaVantageAdapter.delay_requests
        # lock_dir = os.path.join(date_dir, '.lock_{}'.format(id))
        file_id = "{}.{}".format(data_id, datetime.now().strftime("%Y%m%d_%H%M%S_%f")) if timestamp else data_id
        # file_id = "{}.{}".format(data_id, round(datetime.utcnow().timestamp() * 1000)) if timestamp else data_id
        if data_type == DataType.JSON:
            ext = 'json'
        elif data_type == DataType.DATAFRAME:
            ext = 'pickle'
        elif data_type == DataType.CSV:
            ext = 'csv'
        else:
            raise RuntimeError("Unknown data type: {}".format(data_type))
        cache_dir = self.get_cache_dir()
        data_file = os.path.join(cache_dir, 'data.{}.{}'.format(file_id, ext))
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        return data_file, lock_dir

    def get_single_query_lock_dir(self):
        return os.path.join(self.cache_root_dir, '.lock.single_query')

    def get_cache_dir(self):
        return os.path.join(self.cache_root_dir, self.cache_key_date.strftime('%Y%m%d'))

    def clean_cache_dirs(self, keep: int = 3):
        if not os.path.exists(self.cache_root_dir):
            return
        for filename in sorted(os.listdir(self.cache_root_dir))[:-keep]:
            path = os.path.join(self.cache_root_dir, filename)
            shutil.rmtree(path, ignore_errors=True)

    @staticmethod
    def lock(data_file, lock_dir):
        wait = os.path.exists(lock_dir) or not os.path.exists(data_file)
        acquired_lock = False
        while wait:
            if os.path.exists(lock_dir):
                logging.debug("Waiting on lock: {}".format(lock_dir))
                time.sleep(1)  # wait for other process to finish their query
            else:
                try:
                    logging.debug("Attempting to lock: {}".format(lock_dir))
                    os.makedirs(lock_dir)
                    logging.debug("Acquired lock: {}".format(lock_dir))
                    acquired_lock = True
                    break
                except OSError:
                    pass
        return acquired_lock

    def get_adjusted_ratio(self, time_data: Dict[str, str]) -> float:
        """
        Some data sources provide the stock values as they were and an adjusted close value. This is generally to
        account for stock splits. To fix these just different close/adjusted_close = ratio and then ratio *_price to
        get the correct price to account for current splits etc.
        The default here is to return 1.0 so that no adjusting is done by default and override as needed.
        See AlphaVantage as an example of how this is used.
        :param time_data:
        :return:
        """
        return 1.0  # default is to not adjust

    def get_response_value(self, time_data: Dict[str, str], key: str) -> float:
        price = self.get_response_value_or_none(time_data, key)
        if price is None:
            raise RuntimeError('Failed to find response value matching key \'{}\' in \'{}\''.format(key, time_data))
        return price

    @staticmethod
    def get_response_value_or_none(time_data: Dict[str, str], key: str) -> Optional[float]:
        value = float(time_data[key]) if key in time_data else None
        return value

    def validate_data(self, data_file: str):
        pass

    def delay_requests(self, data_file: str):
        # some APIs limit number of requests, this enables client requests for specific providers to match those limtis
        pass

    # def get_sma_data(self, symbol, time_period, series_type):
    #     if symbol not in self.cachedData:
    #         self.cachedData[symbol] = {}
    #     if ValueType.SMA not in self.cachedData[symbol]:
    #         asset_type = self.explicitSymbolTypes[symbol] if symbol in self.explicitSymbolTypes else None
    #         self.cachedData[symbol][ValueType.SMA] = self.get_sma_response(asset_type, symbol, time_period,
    #         series_type)
    #     return self.cachedData[symbol][ValueType.SMA]

    @staticmethod
    def get_date_format():
        return '%Y-%m-%d'

    def calculate_asset_type(self, force: bool = False):
        if self.asset_type is not None and not force:
            logging.debug("Leaving asset type {} for {}".format(self.asset_type.value, self.symbol))
        elif self.asset_type is None:
            is_digital = self.get_is_digital_currency()
            is_equity = self.get_is_listed()
            assert is_digital or is_equity, "Symbol is not a digital currency nor listed: {}".format(self.symbol)
            assert is_digital != is_equity, "Ambiguous symbol is digital currency and is listed: {}".format(self.symbol)
            if is_digital:
                self.asset_type = AssetType.DIGITAL_CURRENCY
            elif is_equity:
                self.asset_type = AssetType.EQUITY
        elif self.asset_type == AssetType.DIGITAL_CURRENCY:
            assert self.get_is_digital_currency(), "Asset type set as {}, but validation failed for: {}".format(
                self.asset_type, self.symbol)
        elif self.asset_type == AssetType.EQUITY:
            assert self.get_is_listed(), "Asset type set as {}, but validation failed for: {}".format(
                self.asset_type, self.symbol)
        logging.debug("Using asset type {} for {}".format(self.asset_type.value, self.symbol))

    def get_is_digital_currency(self) -> bool:
        raise NotImplementedError("Implement: {}".format(inspect.currentframe().f_code.co_name))

    def get_is_listed(self) -> bool:
        raise NotImplementedError("Implement: {}".format(inspect.currentframe().f_code.co_name))

    def get_is_physical_currency(self) -> bool:
        raise NotImplementedError("Implement: {}".format(inspect.currentframe().f_code.co_name))

    # def get_sma_response(self, asset_type, symbol, time_period, value_type):
    #     raise NotImplementedError("Implement: {}".format(inspect.currentframe().f_code.co_name))

    def get_value(self, instance: datetime, value_type: ValueType) -> float:
        assert value_type in self.data, 'The value type {} does not exist in the dataset for time: {}'.format(
            value_type, instance)
        return self.data.loc[instance, value_type]

    def get_all_times(self) -> pandas.Index:
        return self.data.index

    def get_all_values(self, value_type: ValueType) -> pandas.Series:
        return self.data[value_type]

    def get_row(self, instance: datetime) -> pandas.Series:
        return self.data.loc[instance, :]

    def get_column_on_or_before(self, before: datetime, value_type: ValueType) -> pandas.Series:
        filtered: pandas.DataFrame = self.data[self.data.index <= before]
        return filtered[value_type] if value_type in filtered.columns else pandas.Series()

    def get_column_on_or_after(self, after: datetime, value_type: ValueType) -> pandas.Series:
        filtered: pandas.DataFrame = self.data[self.data.index >= after]
        return filtered[value_type] if value_type in filtered.columns else pandas.Series()

    def get_column_between(self, after: datetime, before: datetime, value_type: ValueType) -> pandas.Series:
        filtered: pandas.DataFrame = self.data[self.data.index >= after]
        filtered = filtered[filtered.index <= before]
        return filtered[value_type] if value_type in filtered.columns else pandas.Series()

    def get_all_data_flat(self) -> (Dict[datetime, List[float]], List[ValueType]):
        data = {}
        columns = []
        for date, row in self.data.items():
            data[date] = []
            for key, value in row.items():
                data[date].append(value)
                if key not in columns:
                    columns.append(key)
        return data, columns

    def retrieve(self, value_type: ValueType) -> None:
        converter: Converter = self.get_converter(value_type)
        converter.get_response_callback()

    def get_column(self, value_type: ValueType) -> pandas.Series:
        return self.data[value_type]

    def get_start_time(self) -> Optional[datetime]:
        times = self.get_all_times()
        return None if times.empty else times[0]

    def get_end_time(self) -> Optional[datetime]:
        times = self.get_all_times()
        return None if times.empty else times[-1]

    def find_closest_instance_before(self, instance: datetime) -> Optional[datetime]:
        #### PERFORMANT
        ## Attempt 3
        # self.data.index.sub(instance).abs().idxmin()
        ## Attempt 2
        # closest = self.data[self.data.index <= instance].index.max()
        # if closest is None:
        #     closest = self.data.index.min()
        ## Attempt 1
        indexes: numpy.ndarray = self.data.index.to_numpy()
        all_before = indexes[numpy.where(indexes <= instance)]
        all_before = sorted(all_before, reverse=True)
        closest: Optional[datetime] = all_before[0] if len(all_before) > 0 else None
        # for current in indexes:
        #     if (current < instance) and ((closest is None) or (current > closest)):
        #         closest = current
        #### NEW
        # closest: Optional[datetime] = None
        # closest = self.data[self.data.index <= instance].index.max()
        # if closest is None:
        #     closest = self.data.index.min()
        #### OLD
        # closest: Optional[datetime] = None
        # for current in self.data.index:
        #     if (current < instance) and ((closest is None) or (current > closest)):
        #         closest = current
        return closest

    def find_closest_instance_after(self, instance: datetime) -> Optional[datetime]:
        #### From before (above)
        indexes: numpy.ndarray = self.data.index.to_numpy()
        all_after = indexes[numpy.where(indexes >= instance)]
        all_after = sorted(all_after, reverse=False)
        closest: Optional[datetime] = all_after[0] if len(all_after) > 0 else None
        #### OLD
        # closest: Optional[datetime] = None
        # for current in self.data.index:
        #     if (current > instance) and ((closest is None) or (current < closest)):
        #         closest = current
        return closest

    def has_time(self, instance) -> bool:
        return instance in self.data

    def find_closest_before_else_after(self, instance: datetime) -> datetime:
        closest = self.find_closest_instance_before(instance)
        closest = self.get_start_time() if closest is None else closest
        return closest

    # def get_highs(self) -> List[float]:
    #     values = self.get_all_values(ValueType.HIGH)
    #     return values
    #
    # def get_lows(self) -> List[float]:
    #     values = self.get_all_values(ValueType.LOW)
    #     return values
    #
    # def get_closes(self) -> List[float]:
    #     values = self.get_all_values(ValueType.CLOSE)
    #     return values
    #
    # def get_opens(self) -> List[float]:
    #     values = self.get_all_values(ValueType.OPEN)
    #     return values

    def add_argument(self, argument: Argument) -> None:
        value = self.get_argument_value(argument.argument_type)
        assert value is None, \
            "Argument value is already specified for '{}', current value is '{}' was attempting to set as '{}'".format(
                argument.argument_type.name, value, argument.value)
        self.arguments.append(argument)

    def get_argument_value(self, arg_type: ArgumentType) -> Optional[Any]:
        values = list(set([argument.value for argument in self.arguments if argument.argument_type == arg_type]))
        return values[0] if len(values) == 1 else None

    def insert_data_column(self, value_type, indexes, values):
        duplicates = [x for x in indexes if indexes.count(x) > 1]
        if len(duplicates) > 0:
            raise DuplicateRawIndexesException(f"Indexes must be unique, yet found duplicates: {duplicates}")
        if len(values) > 0:
            if self.data.shape[0] == 0:
                self.data = pandas.Series(values, index=indexes).to_frame(value_type)
            else:
                column = pandas.Series(values, index=indexes)
                merge_df = column.to_frame(value_type)
                merge_df = merge_df.sort_index(ascending=True)
                reindexed_df = merge_df.reindex(self.data.index, method="nearest")
                oldest_time_before_reindexing = merge_df.index[0]
                newest_time_before_reindexing = merge_df.index[-1]
                reindexed_df = reindexed_df[reindexed_df.index <= newest_time_before_reindexing]
                self.data[value_type] = reindexed_df[reindexed_df.index >= oldest_time_before_reindexing]
            self.data = self.data.sort_index(ascending=True)
