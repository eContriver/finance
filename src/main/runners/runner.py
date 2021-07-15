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
import inspect
from abc import ABCMeta, abstractmethod
from typing import Dict


class Runner(metaclass=ABCMeta):
    run_name: str

    def __init__(self):
        self.run_name = "not_started"

    def start(self) -> bool:
        raise NotImplementedError("Implement: {}".format(inspect.currentframe().f_code.co_name))

    def get_run_name(self) -> str:
        return self.run_name

    def get_config(self) -> Dict:
        raise NotImplementedError("Implement: {}".format(inspect.currentframe().f_code.co_name))

    # @staticmethod
    # def calculate_start_and_end_times(strategies: list[Strategy]):
    #     start_time: Optional[datetime] = None
    #     end_time: Optional[datetime] = None
    #     for strategy in strategies:
    #         current_start = strategy.get_last_start_time()
    #         start_time = current_start if start_time is None or current_start > start_time else start_time
    #         current_end = strategy.get_end_time()
    #         end_time = current_end if end_time is None or current_end < end_time else end_time
    #     return end_time, start_time
    @abstractmethod
    def set_from_config(self, config, config_path):
        pass
