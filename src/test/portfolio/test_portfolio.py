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
from datetime import datetime, timedelta
from typing import List
from unittest import TestCase

import pandas

from main.application.adapter_collection import AdapterCollection
from main.application.value_type import ValueType
from main.portfolio.portfolio import filter_list_times, get_current_value
from test.testing_utils import get_test_adapter_data, create_test_collection_with_data, get_test_symbol, get_test_base_symbol


def get_test_data() -> List[datetime]:
    """
    Produces the test data.
    :return: A list of unsorted datetime values, there is one duplicate in this data (where delta is 0)
    """
    data = []
    for it in range(3):
        data.append(datetime(year=3000, month=2, day=1) + timedelta(weeks=it))
    for it in range(3):
        data.append(datetime(year=3000, month=2, day=1) - timedelta(weeks=it))
    return data


class TestPortfolio(TestCase):
    def test_filter_list_times(self):
        data: List[datetime] = get_test_data()
        start_time: datetime = datetime(year=3000, month=2, day=1) - timedelta(weeks=1)
        end_time: datetime = datetime(year=3000, month=2, day=1) + timedelta(weeks=1)
        filtered_data: List[datetime] = filter_list_times(start_time, end_time, data)
        self.assertEqual(min(filtered_data), start_time)
        self.assertEqual(max(filtered_data), end_time)

    def test_filter_list_times_out_of_bounds(self):
        data: List[datetime] = get_test_data()
        start_time: datetime = datetime(year=3000, month=2, day=1) - timedelta(weeks=10)
        end_time: datetime = datetime(year=3000, month=2, day=1) + timedelta(weeks=10)
        filtered_data: List[datetime] = filter_list_times(start_time, end_time, data)
        self.assertEqual(min(filtered_data), datetime(year=3000, month=2, day=1) - timedelta(weeks=2))
        self.assertEqual(max(filtered_data), datetime(year=3000, month=2, day=1) + timedelta(weeks=2))

    def test_get_current_value(self):
        data: pandas.DataFrame = get_test_adapter_data()
        instance: datetime = data.index[-1]
        symbol: str = get_test_symbol()
        base: str = get_test_base_symbol()
        quantities = {base: 10.0, symbol: 10.0}
        value_type = ValueType.CLOSE
        collection: AdapterCollection = create_test_collection_with_data(symbol, data)
        current_value = get_current_value(instance, collection, quantities, value_type)
        expected_value = quantities[base] + (quantities[symbol] * data.loc[instance, value_type])
        self.assertEqual(current_value, expected_value)
