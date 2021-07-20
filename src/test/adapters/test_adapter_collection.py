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
from cmath import nan
from datetime import datetime, timedelta
from unittest import TestCase

import numpy
import pandas

from main.adapters.adapter import Adapter, AssetType, get_common_start_time, get_common_end_time, \
    DuplicateRawIndexesException, find_closest_instance_after, find_closest_instance_before
from main.adapters.adapter_collection import AdapterCollection
from main.adapters.value_type import ValueType


def create_test_adapter_with_data():
    adapter: Adapter = Adapter(get_test_symbol(), AssetType.DIGITAL_CURRENCY)
    adapter.data = pandas.DataFrame()
    adapter.get_value_types = [ValueType.CLOSE]
    adapter.data.loc[get_test_start_time(), ValueType.CLOSE] = 1.0
    adapter.data.loc[get_test_common_time(), ValueType.CLOSE] = 2.0
    adapter.data.loc[get_test_end_time(), ValueType.CLOSE] = 3.0
    return adapter


def get_test_symbol():
    return 'TEST'


def get_test_end_time():
    return get_test_common_time() + timedelta(weeks=2)


def get_test_common_time():
    return datetime(year=3000, month=2, day=1)


def get_test_start_time():
    return get_test_common_time() - timedelta(weeks=2)


def create_test_collection_with_data():
    adapter = create_test_adapter_with_data()
    collection: AdapterCollection = AdapterCollection()
    collection.add(adapter)
    return collection


class TestAdapterCollection(TestCase):

    def test_get_end_date(self):
        """
        Tests that get_end_date on a collection returns the correct end date
        :return:
        """
        collection = create_test_collection_with_data()
        self.assertEqual(collection.get_end_time(get_test_symbol(), ValueType.CLOSE), get_test_end_time())

    def test_get_start_date(self):
        """
        Tests that get_start_date on a collection returns the correct start date
        :return:
        """
        collection = create_test_collection_with_data()
        self.assertEqual(collection.get_start_time(get_test_symbol(), ValueType.CLOSE), get_test_start_time())

    # def test_get_row(self):
    #     collection = create_test_collection_with_data()
    #     self.assertEqual(collection.get_row(get_test_symbol(), get_test_start_time(), ValueType.CLOSE)[0], 1.0)
    #     self.assertEqual(collection.get_row(get_test_symbol(), get_test_start_time(), ValueType.CLOSE)[1], 2.0)
    #     self.assertEqual(collection.get_row(get_test_symbol(), get_test_start_time(), ValueType.CLOSE)[2], 3.0)

    def test_get_value(self):
        """
        Tests that the get_value off of a collection returns the expected values
        :return:
        """
        collection = create_test_collection_with_data()
        self.assertEqual(collection.get_value(get_test_symbol(), get_test_start_time(), ValueType.CLOSE), 1.0)
        self.assertEqual(collection.get_value(get_test_symbol(), get_test_common_time(), ValueType.CLOSE), 2.0)
        self.assertEqual(collection.get_value(get_test_symbol(), get_test_end_time(), ValueType.CLOSE), 3.0)
