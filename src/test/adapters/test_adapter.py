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
from main.adapters.value_type import ValueType


class TestAdapter(TestCase):

    def test_get_common_end_time_no_data(self):
        """
        Test that if we have no data that we get None
        :return:
        """
        data = pandas.DataFrame()
        time_to_check = get_common_end_time(data)
        self.assertIsNone(time_to_check)

    def test_get_common_end_time_no_overlap(self):
        """
        Test that if we have non-overlapping data that we get the end time
        :return:
        """
        data = pandas.DataFrame()
        common_time = datetime(year=3000, month=2, day=1)
        data.loc[common_time + timedelta(weeks=2), ValueType.OPEN] = 1.0
        data.loc[common_time + timedelta(weeks=1), ValueType.OPEN] = 1.0
        data.loc[common_time - timedelta(weeks=1), ValueType.CLOSE] = 1.0
        data.loc[common_time, ValueType.CLOSE] = 1.0
        time_to_check = get_common_end_time(data)
        self.assertEqual(time_to_check, common_time, "Did not get the correct common end time")

    def test_get_common_end_time_with_none(self):
        """
        Ensures that the common end time for multiple columns with differing end dates returns the common end time
        :return:
        """
        data = pandas.DataFrame()
        common_time = datetime(year=3000, month=2, day=1)
        data.loc[common_time + timedelta(weeks=1), ValueType.OPEN] = 1.0
        data.loc[common_time, ValueType.OPEN] = 1.0
        data.loc[common_time - timedelta(weeks=1), ValueType.OPEN] = 1.0
        data.loc[common_time + timedelta(weeks=1), ValueType.CLOSE] = None
        data.loc[common_time, ValueType.CLOSE] = 1.0
        data.loc[common_time - timedelta(weeks=1), ValueType.CLOSE] = 1.0
        time_to_check = get_common_end_time(data)
        self.assertEqual(time_to_check, common_time, "Did not get the correct common end time")

    def test_get_common_start_time_no_data(self):
        """
        Test that if we have no data that we get None
        :return:
        """
        data = pandas.DataFrame()
        time_to_check = get_common_start_time(data)
        self.assertIsNone(time_to_check)

    def test_get_common_start_time_no_overlap(self):
        """
        Test that if we have non-overlapping data that we get the start time
        D1  1    None
        D2  1    None
        D3  None 1     <- Returns D3 assuming sorted indices D1 is less than D2 in datetime (epoch)
        D4  None 1
        :return:
        """
        data = pandas.DataFrame()
        common_time = datetime(year=3000, month=2, day=1)
        data.loc[common_time - timedelta(weeks=2), ValueType.OPEN] = 1.0
        data.loc[common_time - timedelta(weeks=1), ValueType.OPEN] = 1.0
        data.loc[common_time + timedelta(weeks=1), ValueType.CLOSE] = 1.0
        data.loc[common_time, ValueType.CLOSE] = 1.0
        time_to_check = get_common_start_time(data)
        self.assertEqual(time_to_check, common_time, "Did not get the correct common start time")

    def test_get_common_start_time_with_none(self):
        """
        Ensures that the common start time for multiple columns with differing start dates returns the common start time
        :return:
        """
        common_time = datetime(year=3000, month=2, day=1)
        data = pandas.DataFrame()
        data.loc[common_time + timedelta(weeks=1), ValueType.OPEN] = 1.0
        data.loc[common_time, ValueType.OPEN] = 1.0
        data.loc[common_time - timedelta(weeks=1), ValueType.OPEN] = 1.0
        data.loc[common_time + timedelta(weeks=1), ValueType.CLOSE] = 1.0
        data.loc[common_time, ValueType.CLOSE] = 1.0
        data.loc[common_time - timedelta(weeks=1), ValueType.CLOSE] = None
        time_to_check = get_common_start_time(data)
        self.assertEqual(time_to_check, common_time, "Did not get the correct common start time")

    def test_insert_data_column_duplicates_fail(self):
        """
        Check that if data is inserted with duplicate indexes that the DuplicateRawIndexesException is thrown
        :return:
        """
        adapter: Adapter = Adapter('TEST', AssetType.DIGITAL_CURRENCY)
        common_time = datetime(year=3000, month=2, day=1)
        indexes = [common_time, common_time]
        values = [1.0, 1.0]
        self.assertRaises(DuplicateRawIndexesException, adapter.insert_data_column, ValueType.OPEN, indexes, values)

    def test_insert_data_column(self):
        """
        Check that the data column is correctly inserted and sorted as expected
        :return:
        """
        adapter: Adapter = Adapter('TEST', AssetType.DIGITAL_CURRENCY)
        common_time = datetime(year=3000, month=2, day=1)
        open_indexes = [common_time - timedelta(weeks=1), common_time]
        open_values = [1.0, 2.0]
        adapter.insert_data_column(ValueType.OPEN, open_indexes, open_values)
        self.assertEqual(open_values[0], adapter.data.loc[common_time - timedelta(weeks=1), ValueType.OPEN],
                         "First open value was not as expected")
        self.assertEqual(adapter.data[ValueType.OPEN][0], open_values[0], "Open value order was not as expected")
        # NOTICE: The time indexes are swapped... so should the values be
        close_indexes = [common_time + timedelta(weeks=1), common_time]
        close_values = [4.0, 3.0]
        adapter.insert_data_column(ValueType.CLOSE, close_indexes, close_values)
        self.assertEqual(close_values[1], adapter.data.loc[common_time, ValueType.CLOSE],  # ... swapped value
                         "First close value was not as expected")
        self.assertTrue(numpy.isnan(adapter.data[ValueType.CLOSE][0]), "Close value order was not as expected")
        self.assertEqual(adapter.data[ValueType.CLOSE][-1], close_values[0], "Close value order was not as expected")

    def test_find_closest_instance_after_mismatch(self):
        """
        Verify that the closest instance after a mismatched time is returned
        :return:
        """
        adapter: Adapter = Adapter('TEST', AssetType.DIGITAL_CURRENCY)
        adapter.data = pandas.DataFrame()
        common_time = datetime(year=3000, month=2, day=1)
        mismatch_time = common_time - timedelta(weeks=1)
        adapter.data.loc[common_time - timedelta(weeks=2), ValueType.CLOSE] = 1.0
        adapter.data.loc[common_time, ValueType.CLOSE] = 1.0
        adapter.data.loc[common_time + timedelta(weeks=2), ValueType.CLOSE] = 1.0
        self.assertEqual(find_closest_instance_after(adapter.data, mismatch_time), common_time,
                         f"Did not get the correct common end time, expected {common_time}, "
                         f"received {get_common_end_time(adapter.data)}")
        return True

    def test_find_closest_instance_before_mismatch(self):
        """
        Verify that the closest instance before a mismatched time is returned
        :return:
        """
        adapter: Adapter = Adapter('TEST', AssetType.DIGITAL_CURRENCY)
        adapter.data = pandas.DataFrame()
        common_time = datetime(year=3000, month=2, day=1)
        mismatch_time = common_time + timedelta(weeks=1)
        adapter.data.loc[common_time - timedelta(weeks=2), ValueType.CLOSE] = 1.0
        adapter.data.loc[common_time, ValueType.CLOSE] = 1.0
        adapter.data.loc[common_time + timedelta(weeks=2), ValueType.CLOSE] = 1.0
        self.assertEqual(find_closest_instance_before(adapter.data, mismatch_time), common_time,
                         f"Did not get the correct common end time, expected {common_time}, "
                         f"received {get_common_end_time(adapter.data)}")

    def test_get_all_values(self):
        """
        Tests the adapter get_all_values, and checks that out-of-order data works as expected
        :return:
        """
        adapter: Adapter = Adapter('TEST', AssetType.DIGITAL_CURRENCY)
        adapter.data = pandas.DataFrame()
        common_time = datetime(year=3000, month=2, day=1)
        adapter.data.loc[common_time - timedelta(weeks=2), ValueType.CLOSE] = 1.0
        adapter.data.loc[common_time, ValueType.CLOSE] = 2.0
        adapter.data.loc[common_time + timedelta(weeks=2), ValueType.CLOSE] = 3.0
        self.assertEqual(adapter.get_all_values(ValueType.CLOSE)[0], 1.0)
        self.assertEqual(adapter.get_all_values(ValueType.CLOSE)[1], 2.0)
        self.assertEqual(adapter.get_all_values(ValueType.CLOSE)[2], 3.0)
        adapter.data.loc[common_time - timedelta(weeks=4), ValueType.CLOSE] = 0.5
        self.assertEqual(adapter.get_all_values(ValueType.CLOSE)[3], 0.5)

    def test_get_row(self):
        """
        Tests the adapter get_row, and checks that out-of-order data works as expected
        :return:
        """
        adapter: Adapter = Adapter('TEST', AssetType.DIGITAL_CURRENCY)
        adapter.data = pandas.DataFrame()
        common_time = datetime(year=3000, month=2, day=1)
        adapter.data.loc[common_time - timedelta(weeks=2), ValueType.CLOSE] = 1.0
        adapter.data.loc[common_time, ValueType.CLOSE] = 2.0
        adapter.data.loc[common_time + timedelta(weeks=2), ValueType.CLOSE] = 3.0
        self.assertEqual(adapter.get_row(common_time)[ValueType.CLOSE], 2.0)

    def test_get_value(self):
        """
        Tests the adapter get_value, and checks that out-of-order data works as expected
        :return:
        """
        adapter: Adapter = Adapter('TEST', AssetType.DIGITAL_CURRENCY)
        adapter.data = pandas.DataFrame()
        common_time = datetime(year=3000, month=2, day=1)
        adapter.data.loc[common_time - timedelta(weeks=2), ValueType.CLOSE] = 1.0
        adapter.data.loc[common_time, ValueType.CLOSE] = 2.0
        adapter.data.loc[common_time + timedelta(weeks=2), ValueType.CLOSE] = 3.0
        self.assertEqual(adapter.get_value(common_time - timedelta(weeks=2), ValueType.CLOSE), 1.0)
        self.assertEqual(adapter.get_value(common_time, ValueType.CLOSE), 2.0)
        self.assertEqual(adapter.get_value(common_time + timedelta(weeks=2), ValueType.CLOSE), 3.0)
        adapter.data.loc[common_time - timedelta(weeks=4), ValueType.CLOSE] = 0.5
        self.assertEqual(adapter.get_value(common_time - timedelta(weeks=4), ValueType.CLOSE), 0.5)

