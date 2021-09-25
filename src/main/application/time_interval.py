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

from datetime import timedelta
from enum import Enum


class TimeInterval(Enum):
    """
    The TimeInterval enumeration is intended to represent the time intervals between data. It is generally used when
    querying an adapter for data as most APIs require an interval.

    The TimeInterval class is also used when saving and reading configuration information from configuration files.

    The string value can be used for messages, but it's purpose is for human readable files such as configuration files
    etc. The timedelta value is intended to be used for calculations and comparisons between the time intervals.

    Retrieve the values as:
      TimeValue.SEC15.value -> '15sec'
      TimeValue.SEC15.timedelta -> timedelta(seconds=15)
    """
    SEC15 = '15sec', timedelta(seconds=15)
    MIN1 = '1min', timedelta(minutes=1)
    MIN5 = '5min', timedelta(minutes=5)
    MIN10 = '10min', timedelta(minutes=10)
    MIN15 = '15min', timedelta(minutes=15)
    MIN30 = '30min', timedelta(minutes=30)
    HOUR = 'hourly', timedelta(hours=1)
    HOUR6 = '6hour', timedelta(hours=6)
    DAY = 'daily', timedelta(days=1)
    WEEK = 'weekly', timedelta(weeks=1)
    MONTH = 'monthly', timedelta(days=30)  # hmm?
    QUARTER = 'quarterly', timedelta(weeks=13)
    YEAR = 'yearly', timedelta(weeks=52)
    YEAR2 = '2year', timedelta(weeks=52 * 2)
    YEAR5 = '5year', timedelta(weeks=52 * 5)

    def __new__(cls, value, delta):
        member = object.__new__(cls)
        member._value_ = value
        member.timedelta = delta
        return member