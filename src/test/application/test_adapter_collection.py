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

#
#
#
from unittest import TestCase

import pandas

from main.application.adapter_collection import AdapterCollection
from main.application.value_type import ValueType
from test.testing_utils import get_test_adapter_data, get_test_symbol, \
    create_test_collection_with_data


class TestAdapterCollection(TestCase):

    def test_get_end_date(self):
        """
        Checks that get_end_date on a collection returns the correct end date.
        :return:
        """
        data: pandas.DataFrame = get_test_adapter_data()
        symbol: str = get_test_symbol()
        collection: AdapterCollection = create_test_collection_with_data(symbol, data)
        self.assertEqual(collection.get_end_time(symbol, ValueType.CLOSE), data.index[-1])

    def test_get_start_date(self):
        """
        Checks that get_start_date on a collection returns the correct start date.
        :return:
        """
        data: pandas.DataFrame = get_test_adapter_data()
        symbol: str = get_test_symbol()
        collection: AdapterCollection = create_test_collection_with_data(symbol, data)
        self.assertEqual(collection.get_start_time(symbol, ValueType.CLOSE), data.index[0])

    def test_get_value(self):
        """
        Checks that the get_value off of a collection returns the expected values.
        :return:
        """
        data: pandas.DataFrame = get_test_adapter_data()
        symbol: str = get_test_symbol()
        collection: AdapterCollection = create_test_collection_with_data(symbol, data)
        for index in data.index:
            self.assertEqual(collection.get_value(symbol, index, ValueType.CLOSE), data.loc[index, ValueType.CLOSE])
