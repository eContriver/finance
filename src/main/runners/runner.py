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

from main.common.locations import Locations


class Runner(metaclass=ABCMeta):

    def __init__(self):
        pass

    @abstractmethod
    def start(self, locations: Locations) -> bool:
        pass

    @abstractmethod
    def get_run_name(self) -> str:
        pass

    @abstractmethod
    def get_config(self) -> Dict:
        pass

    @abstractmethod
    def set_from_config(self, config, config_path):
        pass


class NoSymbolsSpecifiedException(RuntimeError):
    pass