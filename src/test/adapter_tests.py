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

import pandas

from main.adapters.adapter import Adapter, AssetType, find_closest_instance_before
from main.adapters.adapter_collection import AdapterCollection
from main.adapters.value_type import ValueType
from test.runner_test import only_test, is_test
from test.utils_test import setup_collection





@is_test
# @only_test
def verify_find_closest_instance_before():
    adapter: Adapter = Adapter('TEST', AssetType.DIGITAL_CURRENCY)
    adapter.data = pandas.DataFrame()
    common_time = datetime(year=3000, month=2, day=1)
    adapter.data.loc[common_time - timedelta(weeks=2), ValueType.CLOSE] = 1.0
    adapter.data.loc[common_time, ValueType.CLOSE] = 1.0
    adapter.data.loc[common_time + timedelta(weeks=2), ValueType.CLOSE] = 1.0
    assert find_closest_instance_before(adapter.data,
                                        common_time) == common_time, f"Did not get the correct common end time, expected {common_time}, received {get_common_end_time(adapter.data)}"
    return True


@is_test
# @only_test
def verify_find_closest_instance_after():
    adapter: Adapter = Adapter('TEST', AssetType.DIGITAL_CURRENCY)
    adapter.data = pandas.DataFrame()
    common_time = datetime(year=3000, month=2, day=1)
    adapter.data.loc[common_time - timedelta(weeks=2), ValueType.CLOSE] = 1.0
    adapter.data.loc[common_time, ValueType.CLOSE] = 1.0
    adapter.data.loc[common_time + timedelta(weeks=2), ValueType.CLOSE] = 1.0
    assert find_closest_instance_after(adapter.data,
                                       common_time) == common_time, f"Did not get the correct common end time, expected {common_time}, received {get_common_end_time(adapter.data)}"
    return True


@is_test
# @only_test
def verify_common_end():
    adapter: Adapter = Adapter('TEST', AssetType.DIGITAL_CURRENCY)
    adapter.data = pandas.DataFrame()
    common_time = datetime(year=3000, month=2, day=1)
    adapter.data.loc[common_time - timedelta(weeks=1), ValueType.OPEN] = 1.0
    adapter.data.loc[common_time, ValueType.OPEN] = 1.0
    adapter.data.loc[common_time - timedelta(weeks=1), ValueType.CLOSE] = 1.0
    adapter.data.loc[common_time, ValueType.CLOSE] = 1.0
    adapter.data.loc[common_time + timedelta(weeks=1), ValueType.CLOSE] = 1.0
    assert get_common_end_time(
        adapter.data) == common_time, f"Did not get the correct common end time, expected {common_time}, received {get_common_end_time(adapter.data)}"
    return True
