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
from enum import Enum, auto
from typing import Any

from main.application.time_interval import TimeInterval


class ArgumentKey(Enum):
    INTERVAL = auto()
    START_TIME = auto()
    END_TIME = auto()
    # RSI_INTERVAL = auto()
    RSI_PERIOD = auto()
    # SMA_INTERVAL = auto()
    SMA_PERIOD = auto()
    MACD_SLOW = auto()
    MACD_FAST = auto()
    MACD_SIGNAL = auto()
    BOOK = auto()


def get_argument_type(argument_key: ArgumentKey):
    types = {
        ArgumentKey.INTERVAL: TimeInterval,
        ArgumentKey.START_TIME: datetime,
        ArgumentKey.END_TIME: datetime,
        ArgumentKey.RSI_PERIOD: float,
        ArgumentKey.SMA_PERIOD: float,
        ArgumentKey.MACD_SLOW: float,
        ArgumentKey.MACD_FAST: float,
        ArgumentKey.MACD_SIGNAL: float,
        ArgumentKey.BOOK: float,
    }
    return types.get(argument_key)


class Argument:
    value: Any
    argument_key: ArgumentKey

    def __init__(self, argument_key: ArgumentKey, value: Any):
        self.argument_key = argument_key
        assert isinstance(value, get_argument_type(argument_key))
        self.value = value
