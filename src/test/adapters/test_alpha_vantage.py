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
import logging
from datetime import timedelta, datetime
from unittest import TestCase

from main.application.adapter import request_limit_with_timedelta_delay
from test import utils_test


class TestAlphaVantage(TestCase):
    def test_delay_requests(self):
        utils_test.configure_test_logging()
        start_time = datetime.now()
        historic_requests = {
            '/path1': start_time,
            '/path2': start_time,
            '/path3': start_time,
            '/path4': start_time,
            '/path5': start_time,
        }
        max_timeframe = timedelta(milliseconds=500)
        request_limit_with_timedelta_delay(buffer=0.0, historic_requests=historic_requests,
                                           max_timeframe=max_timeframe, max_requests=5)
        request_limit_with_timedelta_delay(buffer=0.0, historic_requests=historic_requests,
                                           max_timeframe=max_timeframe, max_requests=5)
        end_time = datetime.now()
        delta_time = end_time - start_time
        self.assertLessEqual(max_timeframe, delta_time)
