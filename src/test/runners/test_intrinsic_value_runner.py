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

import pandas

from main.application.adapter import Adapter, insert_data_column
from main.application.adapter_collection import filter_adapters, AdapterCollection
from main.application.value_type import ValueType
from main.runners.intrinsic_value_runner import predict_value_type_linear, predict_value_linear
from test.testing_utils import get_test_adapter_data, get_test_symbol, \
    create_test_collection_with_data, get_test_time_delta


class TestIntrinsicValueRunner(TestCase):
    def test_predict_future_value_linear_is_accurate(self):
        """
        Tests that with the linear prediction will predict the next value
        D1: 1.0
        D2: 2.0
        D3: 3.0
        :return:
        """
        data: pandas.DataFrame = get_test_adapter_data()
        symbol: str = get_test_symbol()
        collection: AdapterCollection = create_test_collection_with_data(symbol, data)
        future_time: datetime = data.index[-1] + get_test_time_delta()
        next_value = predict_value_type_linear(collection, symbol, ValueType.CLOSE, future_time)
        # 1 -> 2 -> 3 so predict -> 4
        self.assertAlmostEqual(next_value, 4.0)

    def test_predict_future_value_linear_handles_na(self):
        """
        Tests that with a nan value in the data the linear prediction will still do what is desired
        D1: 1.0 1.0
        D2: 2.0 nan
        D3: 3.0 2.0
        :return:
        """
        data: pandas.DataFrame = get_test_adapter_data()
        symbol: str = get_test_symbol()
        collection: AdapterCollection = create_test_collection_with_data(symbol, data)
        adapter: Adapter = filter_adapters(collection.adapters, 'TEST', ValueType.CLOSE)
        adapter.request_value_types.append(ValueType.OPEN)
        start_time: datetime = data.index[0]
        end_time: datetime = data.index[-1]
        insert_data_column(adapter.data, ValueType.OPEN, [start_time, end_time], [1.0, 2.0])
        future_time: datetime = end_time + get_test_time_delta(2)
        next_value = predict_value_type_linear(collection, 'TEST', ValueType.OPEN, future_time)
        self.assertAlmostEqual(next_value, 3.0)  # D5 equivalent

    def test_predict_value_linear_is_accurate(self):
        data: pandas.DataFrame = get_test_adapter_data()
        column: pandas.Series = data[ValueType.CLOSE]
        future_time = (column.index.max() - column.index.min()) + column.index.max()
        expected_value = column.iloc[-1] - column.iloc[0] + column.iloc[-1]
        future_value = predict_value_linear(column, future_time)
        self.assertAlmostEqual(expected_value, future_value)
