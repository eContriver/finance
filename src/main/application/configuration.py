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
import os
from typing import Any, Dict, Hashable

import yaml


class Configuration:

    data: Dict[Hashable, Any]

    def __init__(self):
        self.data = {}

    def read_yaml_config_file(self, config_path: str):
        """
        Read a YAML file into a Python data structure that can be used to access the data and set properties of objects.
        This method uses the safe_load method which is known to be safe with unknown YAML files. This means that we have to
        manually translate arguments (like Adapters class names) from strings into the objects, but this prevents malicious
        actors from being able to inject executable snippets into the YAML and then sharing it with others.
        :param config_path: The location of the YAML file that will be read
        :return: The Python representation of the data that was read from the YAML file
        """
        logging.debug(f"Reading YAML config file: file://{config_path}")
        with open(config_path) as infile:
            self.data = yaml.safe_load(infile)

    def write_yaml_config_file(self, config_path: str) -> None:
        """
        Write a YAML file with the configuration of a Runner. This is generally used to write the arguments of a run
        next to the report of a run for reproducibility and for sharing purposes.
        :param config_path: The location of the configuration file to write out
        :return:
        """
        logging.debug(f"Writing YAML config file: file://{config_path}")
        output_dir: str = os.path.dirname(config_path)
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)
        with open(config_path, 'w') as outfile:
            yaml.dump(self.data, outfile, default_flow_style=False)

    def get_or_default(self, key: str, default: Any) -> Any:
        return self.data[key] if key in self.data else default
