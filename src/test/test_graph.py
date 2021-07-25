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
from time import sleep
from unittest import TestCase

import pandas

from main.adapters.value_type import ValueType
from main.visual.pane import Pane
from test.adapters.test_adapter_collection import get_test_start_time, get_test_end_time, get_test_common_time
import matplotlib.pyplot as plt

class TestGraph(TestCase):
    def test_dataframe_plot(self):
        # df = pandas.DataFrame()
        # df.loc[get_test_start_time(), ValueType.CLOSE] = 100.0
        # df.loc[get_test_common_time(), ValueType.CLOSE] = 200.0
        # df.loc[get_test_end_time(), ValueType.CLOSE] = 300.0
        # df.plot()
        # plt.show(block=True)
        pass

    def test_to_json(self):
        # sleep(10)
        pane = Pane()
