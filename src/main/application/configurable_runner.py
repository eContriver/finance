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
import os
from abc import ABC, abstractmethod
from argparse import Namespace
from datetime import datetime
from typing import Dict

from main.application.configuration import Configuration
from main.application.runner import Runner, prepare_run, finish_run
from main.common.locations import Locations, file_link_format
from main.common.report import Report


class ConfigurableRunner(Runner, ABC):

    config: Configuration

    def __init__(self):
        super().__init__()
        self.config = Configuration()

    def run(self, locations: Locations, args: Namespace) -> bool:
        """
        A standard entry point to run this class. The start method is called by this method and start must be
        implemented by the subclasses.
        :param locations: The Locations that were configured from command-line/configuration files
        :param args: The parsed args
        :return: A bool that represents
        """
        success = True
        run_start = datetime.now()
        prepare_run(locations, args.debug, args.profile)
        if 'config_path' in args:
            try:
                self.config.read_yaml_config_file(args.config_path)
                self.set_from_config(self.config)
            except KeyError as e:
                raise MissingConfigKeyException(f"While parsing {file_link_format(args.config_path)} failed to find "
                                                f"expected key: {e}")
        success = success and self.start(locations)
        if 'config_path' in args:
            output_dir = locations.get_output_dir(Report.camel_to_snake(self.__class__.__name__))
            config_path = os.path.join(output_dir, f"{self.get_run_name()}.yaml")
            self.config.data = self.get_config()
            self.config.write_yaml_config_file(config_path)
        finish_run(run_start, args.profile)
        return success

    @abstractmethod
    def get_config(self) -> Dict:
        pass

    @abstractmethod
    def set_from_config(self, config: Configuration):
        pass


class MissingConfigKeyException(KeyError):
    """
    This exception is thrown while parsing YAML configuration files and just adds the currently processing configuration
    file to the error message.
    """
    pass


class TooManySymbolsSpecifiedException(RuntimeError):
    """
    """
    pass


class NoSymbolsSpecifiedException(RuntimeError):
    """
    If the runner does not have any symbols specified then this exception can be thrown. This is intended for classes
    extending the Runner class. Most Runner subclasses will be using a YAML file to do configuration and this can be
    used in cases where the user has forgotten to specify a symbol in teh YAML file.
    """
    pass