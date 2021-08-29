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
from unittest import TestCase

import numpy
import pandas

from main.application.adapter import Adapter, AssetType, get_common_start_time, get_common_end_time, \
    DuplicateRawIndexesException, find_closest_instance_after, find_closest_instance_before, insert_data_column, \
    DataNotSortedException, get_default_cache_key_date, find_closest_before_else_after, \
    get_column, get_key_for_api_request
from main.application.value_type import ValueType
from test.testing_utils import TestDigitalCurrencyAdapter, get_test_adapter_data


def generate_data(data_height: int = 1000, start_time: datetime = datetime(year=3000, month=2, day=1)):
    data = pandas.DataFrame()
    for it in range(data_height):
        data.loc[start_time + (it * timedelta(weeks=1)), ValueType.CLOSE] = it
    mid_time = start_time + ((data_height / 2) * timedelta(weeks=1))
    return data, mid_time


def get_average_runtime(function, args, run_count: int = 10) -> timedelta:
    total_run_time = timedelta()
    for it in range(run_count):
        run_start = datetime.now()
        function(*args)
        run_end = datetime.now()
        total_run_time += run_end - run_start
    average_run_time = total_run_time / run_count
    return average_run_time


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
        adapter: Adapter = TestDigitalCurrencyAdapter('TEST', AssetType.DIGITAL_CURRENCY)
        common_time = datetime(year=3000, month=2, day=1)
        indexes = [common_time, common_time]
        values = [1.0, 1.0]
        self.assertRaises(DuplicateRawIndexesException, insert_data_column, adapter.data, ValueType.OPEN, indexes,
                          values)

    def test_insert_data_column(self):
        """
        Check that the data column is correctly inserted and sorted as expected
        :return:
        """
        adapter: Adapter = TestDigitalCurrencyAdapter('TEST', AssetType.DIGITAL_CURRENCY)
        common_time = datetime(year=3000, month=2, day=1)
        start_time = common_time - timedelta(weeks=1)
        open_indexes = [start_time, common_time]
        open_values = [1.0, 2.0]
        insert_data_column(adapter.data, ValueType.OPEN, open_indexes, open_values)
        open_time_index = open_indexes.index(common_time)
        self.assertEqual(open_values[open_time_index], adapter.data.loc[common_time, ValueType.OPEN],
                         "First open value was not as expected")
        self.assertEqual(adapter.data[ValueType.OPEN][0], open_values[0], "Open value order was not as expected")
        # NOTICE: The time indexes are swapped... so should the values be...
        end_time = common_time + timedelta(weeks=1)
        close_indexes = [end_time, common_time]  # ... swapped
        close_values = [4.0, 3.0]  # ... swapped
        insert_data_column(adapter.data, ValueType.CLOSE, close_indexes, close_values)
        close_time_index = close_indexes.index(common_time)
        self.assertEqual(close_values[close_time_index], adapter.data.loc[common_time, ValueType.CLOSE],
                         "First close value was not as expected")
        self.assertTrue(numpy.isnan(adapter.data.loc[start_time, ValueType.CLOSE]),
                        "Close value order was not as expected")
        self.assertEqual(adapter.data.loc[common_time, ValueType.CLOSE], close_values[close_time_index],
                         "Close value order was not as expected")
        end_time_index = close_indexes.index(end_time)
        self.assertEqual(adapter.data.loc[end_time, ValueType.CLOSE], close_values[end_time_index],
                         "Close value order was not as expected")

    def test_find_closest_instance_after_raises(self):
        """
        Verify that the closest instance after throws an exception for unsorted data
        :return:
        """
        data: pandas.DataFrame = pandas.DataFrame()
        common_time = datetime(year=3000, month=2, day=1)
        indexes = [common_time, common_time - timedelta(weeks=1)]
        values = [1.0, 1.0]
        insert_data_column(data, ValueType.CLOSE, indexes, values)
        data.sort_index(ascending=False, inplace=True)
        self.assertRaises(DataNotSortedException, find_closest_instance_after, data, common_time)

    def test_find_closest_instance_after_mismatch(self):
        """
        Verify that the closest instance after a mismatched time is returned
        :return:
        """
        adapter: Adapter = TestDigitalCurrencyAdapter('TEST', AssetType.DIGITAL_CURRENCY)
        adapter.data = pandas.DataFrame()
        common_time = datetime(year=3000, month=2, day=1)
        mismatch_time = common_time - timedelta(weeks=1)
        adapter.data.loc[common_time - timedelta(weeks=2), ValueType.CLOSE] = 1.0
        adapter.data.loc[common_time, ValueType.CLOSE] = 1.0
        adapter.data.loc[common_time + timedelta(weeks=2), ValueType.CLOSE] = 1.0
        self.assertEqual(find_closest_instance_after(adapter.data, mismatch_time), common_time,
                         f"Did not get the correct common end time, expected {common_time}, "
                         f"received {get_common_end_time(adapter.data)}")

    def test_find_closest_instance_after_performance(self):
        """
        Verify that the closest instance after a mismatched time is returned
        :return:
        """
        adapter: Adapter = TestDigitalCurrencyAdapter('TEST', AssetType.DIGITAL_CURRENCY)
        adapter.data, mid_time = generate_data()
        average_runtime = get_average_runtime(find_closest_instance_after, (adapter.data, mid_time))
        self.assert_performant_runtime(average_runtime, expected_runtime=timedelta(microseconds=50))

    def test_find_closest_instance_before_raises(self):
        """
        Verify that the closest instance before throws an exception for unsorted data
        :return:
        """
        data: pandas.DataFrame = pandas.DataFrame()
        common_time = datetime(year=3000, month=2, day=1)
        indexes = [common_time, common_time - timedelta(weeks=1)]
        values = [1.0, 1.0]
        insert_data_column(data, ValueType.CLOSE, indexes, values)
        data.sort_index(ascending=False, inplace=True)
        self.assertRaises(DataNotSortedException, find_closest_instance_before, data, common_time)

    def test_find_closest_instance_before_mismatch(self):
        """
        Verify that the closest instance before a mismatched time is returned
        :return:
        """
        adapter: Adapter = TestDigitalCurrencyAdapter('TEST', AssetType.DIGITAL_CURRENCY)
        adapter.data = pandas.DataFrame()
        # index=pd.date_range('1/1/2000', periods=1000)
        # ts = pd.Series(np.random.randn(1000), index=pd.date_range('1/1/2000', periods=1000))
        common_time = datetime(year=3000, month=2, day=1)
        mismatch_time = common_time + timedelta(weeks=1)
        adapter.data.loc[common_time - timedelta(weeks=2), ValueType.CLOSE] = 1.0
        adapter.data.loc[common_time, ValueType.CLOSE] = 1.0
        adapter.data.loc[common_time + timedelta(weeks=2), ValueType.CLOSE] = 1.0
        self.assertEqual(find_closest_instance_before(adapter.data, mismatch_time), common_time,
                         f"Did not get the correct common end time, expected {common_time}, "
                         f"received {get_common_end_time(adapter.data)}")

    def test_find_closest_instance_before_performance(self):
        """
        Verify that the closest instance before a mismatched time is returned
        :return:
        """
        adapter: Adapter = TestDigitalCurrencyAdapter('TEST', AssetType.DIGITAL_CURRENCY)
        adapter.data, mid_time = generate_data()
        average_runtime = get_average_runtime(find_closest_instance_before, (adapter.data, mid_time))
        self.assert_performant_runtime(average_runtime, expected_runtime=timedelta(microseconds=40))

    def assert_performant_runtime(self, average_runtime: timedelta, expected_runtime: timedelta,
                                  allowed_multiple: int = 3):
        allowed_runtime = allowed_multiple * expected_runtime
        self.assertLess(average_runtime, allowed_runtime,
                        f"The runtime was {average_runtime} and was more than {allowed_multiple} times the expected "
                        f"runtime {expected_runtime} (i.e. max allowed {allowed_runtime})")

    def test_get_all_values(self):
        """
        Tests the adapter get_all_values, and checks that out-of-order data works as expected
        :return:
        """
        adapter: Adapter = TestDigitalCurrencyAdapter('TEST', AssetType.DIGITAL_CURRENCY)
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
        adapter: Adapter = TestDigitalCurrencyAdapter('TEST', AssetType.DIGITAL_CURRENCY)
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
        adapter: Adapter = TestDigitalCurrencyAdapter('TEST', AssetType.DIGITAL_CURRENCY)
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

    def test_get_default_cache_key_date(self):
        """
        Tests that the cache key date returned is a datetime
        :return:
        """
        cache_key_date: datetime = get_default_cache_key_date()
        self.assertIsInstance(cache_key_date, datetime)

    def test_find_closest_before_else_after(self):
        """
        Checks that the find closest before else after returns the same if it exists, the before if slightly before, and
        an after value if there is no matching value before the given time.
        :return:
        """
        data: pandas.DataFrame = get_test_adapter_data()
        middle_date = data.index[1]
        self.assertEqual(find_closest_before_else_after(data, middle_date), middle_date)
        start_date = data.index[0]
        just_before_middle = middle_date - timedelta(days=1)
        self.assertEqual(find_closest_before_else_after(data, just_before_middle), start_date)
        just_before_start = start_date - timedelta(days=1)
        self.assertEqual(find_closest_before_else_after(data, just_before_start), start_date)

    def test_get_column(self):
        """
        Checks that the column (series) from a data frame matches with get_column function returns.
        :return:
        """
        data: pandas.DataFrame = get_test_adapter_data()
        column: pandas.Series = get_column(data, ValueType.CLOSE)
        expected_column: pandas.Series = data[ValueType.CLOSE]
        self.assertTrue(column.equals(expected_column))

    def test_get_key_for_api_request(self):
        args = {'key1': 'arg1', 'key2': datetime(year=3000, month=1, day=1), 'arg3': 3.0}
        key: str = get_key_for_api_request(self.test_get_key_for_api_request, args)
        self.assertEqual(key, 'TestAdapter.test_get_key_for_api_request.arg1_3000-01-01_00_00_00_3_0')

    # def test_write_url_response_to_file(self):
    #     configure_test_logging()
    #     locations = Locations()
    #     with subprocess.Popen(["ifconfig"], stdout=subprocess.PIPE) as proc:
    #         strategy_date_dir = get_and_clean_timestamp_dir(locations.get_cache_dir('tests'))
    #         reposonse_url = os.path.join(strategy_date_dir, f'{self.test_write_url_response_to_file.__name__}')
    #         input_file = os.path.join(strategy_date_dir, f'{self.test_write_url_response_to_file.__name__}.in.json')
    #         test_data = {'key1': 'value1', 'key2': 'value2'}
    #         # with open(input_file, "w") as outfile:
    #         #     json.dump(test_data, outfile)
    #         request_url = f"file://{input_file}"
    #         args = {'key1': 'arg1'}
    #         # args = {'key1': 'arg1', 'key2': datetime(year=3000, month=1, day=1), 'arg3': 3.0}
    #         write_url_response_to_file(reposonse_url, args, request_url)
    #     self.fail()
    #     pass
