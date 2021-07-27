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
from datetime import datetime
from unittest import TestCase

from main.application.adapter import Adapter, insert_data_column
from main.application.adapter_collection import AdapterCollection, filter_adapters
from main.application.value_type import ValueType
from main.runners.intrinsic_value_runner import predict_future_value_linear
from test.adapters.test_adapter_collection import create_test_collection_with_data, \
    get_test_end_time, get_test_timedelta, get_test_start_time


class Test(TestCase):
    def test_predict_future_value_linear_is_accurate(self):
        """
        Tests that with the linear prediction will predict the next value
        D1: 1.0
        D2: 2.0
        D3: 3.0
        :return:
        """
        collection: AdapterCollection = create_test_collection_with_data()
        future_time: datetime = get_test_end_time() + get_test_timedelta()
        next_value = predict_future_value_linear('TEST', future_time, collection, ValueType.CLOSE)
        # 1 -> 2 -> 3 so predict -> 4
        self.assertAlmostEqual(next_value, 4.0)

    def test_predict_future_value_linear_handles_na(self):
        """
        Tests that with a nan value in the take the linear prediction will still do what is desired
        D1: 1.0 1.0
        D2: 2.0 nan
        D3: 3.0 2.0
        :return:
        """
        collection: AdapterCollection = create_test_collection_with_data()
        adapter: Adapter = filter_adapters(collection.adapters, 'TEST', ValueType.CLOSE)
        adapter.request_value_types.append(ValueType.OPEN)
        insert_data_column(adapter.data, ValueType.OPEN, [get_test_start_time(), get_test_end_time()],
                                   [1.0, 2.0])
        future_time: datetime = get_test_end_time() + 2 * get_test_timedelta()
        next_value = predict_future_value_linear('TEST', future_time, collection, ValueType.OPEN)
        self.assertAlmostEqual(next_value, 3.0)  # D5 equivalent
