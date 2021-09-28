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
import tempfile
from unittest import TestCase

import yaml

from main.application.configuration import Configuration


# class MockConfigurableRunner(ConfigurableRunner):
#     """
#     This is an example of how the ConfigutableRunner would be used in any of the
#     classes defined in the runner module
#     """
#
#     def get_config(self) -> Dict:
#         pass
#
#     def set_from_config(self, config: Configuration, yaml_file):
#         config = read_yaml_config_file(yaml_file) if os.path.exists(yaml_file) else {}
#         try:
#             self.set_from_config(yaml_file)
#         except KeyError as e:
#             raise MissingConfigKeyException(f"While parsing {file_link_format(yaml_file)} failed to find "
#                                             f"expected key: {e}")
#
#     def start(self, locations: Locations) -> bool:
#         return True
#
#     def get_run_name(self) -> str:
#         return "My Mock Configurable Runner"
#

class TestConfiguration(TestCase):
    def test_read_yaml_config_file(self):
        config: Configuration = Configuration()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "test.yml")
            data = {'test_key': 'test_val'}
            with open(config_path, 'w') as outfile:
                yaml.dump(data, outfile, default_flow_style=False)
            config.read_yaml_config_file(config_path)
            self.assertDictEqual(data, config.data)

    def test_write_yaml_config_file(self):
        config: Configuration = Configuration()
        with tempfile.TemporaryDirectory() as tmpdir:
            data = {'test_key': 'test_val'}
            config.data = data
            config_path = os.path.join(tmpdir, "test.yml")
            config.write_yaml_config_file(config_path)
            with open(config_path) as infile:
                read_data = yaml.safe_load(infile)
            self.assertDictEqual(read_data, data)

