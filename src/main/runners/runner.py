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
from typing import Dict, Any, Optional

from main.common.locations import Locations, file_link_format


class NoSymbolsSpecifiedException(RuntimeError):
    """
    If the runner does not have any symbols specified then this exception can be thrown. This is intended for classes
    extending the Runner class. Most Runner subclasses will be using a YAML file to do configuration and this can be
    used in cases where the user has forgotten to specify a symbol in teh YAML file.
    """
    pass


class Runner(metaclass=ABCMeta):

    def __init__(self):
        pass

    @abstractmethod
    def start(self, locations: Locations) -> bool:
        """
        This method should be implemented with the logic that will execute some calculation, order execution, back
        testing, alerts checks, etc.
        :param locations: The Locations that were configured from command-line/configuration files
        :return: True upon success else false means the runner failed, results are assumed to only be valid if True
        """
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


def validate_type(input_key: str, variable: Any, variable_type: type, config_path: Optional[str] = None):
    if type(variable) is not variable_type:
        path_message = f" (see: {file_link_format(config_path)})"
        raise UnexpectedDataTypeException(f"Input '{input_key}' is expected to be type '{variable_type}', but "
                                          f"instead found: '{type(variable).__name__}'{path_message}")


class UnexpectedDataTypeException(RuntimeError):
    pass