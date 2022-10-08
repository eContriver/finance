# ------------------------------------------------------------------------------
#  Copyright 2021-2022 eContriver LLC
#  This file is part of Finance from eContriver.
#  -
#  Finance from eContriver is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  any later version.
#  -
#  Finance from eContriver is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  -
#  You should have received a copy of the GNU General Public License
#  along with Finance from eContriver.  If not, see <https://www.gnu.org/licenses/>.
# ------------------------------------------------------------------------------

import inspect
from abc import ABCMeta, abstractmethod


class Calculator(metaclass=ABCMeta):
    """
    Indicator is used to perform analysis on a data set such as RSI, MACD, SMA, EMA, etc.
    """

    def __str__(self):
        return f"{self.__class__.__name__} indicator"

    @abstractmethod
    def calc(self, prices_list):
        raise NotImplementedError("Implement: {}".format(inspect.currentframe().f_code.co_name))
