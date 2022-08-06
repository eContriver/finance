#!python

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
import argparse
import glob
import importlib
import logging
import os
import sys
import unittest

from main.application.runner import add_common_arguments
from main.common.locations import Locations
from test.runner_test import TestRunner

g_locations = Locations()
TestRunner.get_instance(g_locations.get_cache_dir('test'))

# NOTE: This code automatically adds all modules in the test directory
test_dir = 'test'
parent_dir = os.path.abspath(os.path.dirname(__file__))
root_dir = os.path.abspath(os.path.join(parent_dir, '..'))
# TODO: failed attempt to match CDing into src and running...
# print(sys.path)
# sys.path.insert(0, root_dir)
# print(sys.path)
for module in os.listdir(os.path.join(parent_dir, test_dir)):
    if module == '__init__.py' or module[-3:] != '.py':
        continue
    logging.debug(f"Importing: {test_dir}.{module[:-3]}")
    importlib.import_module(f'.{module[:-3]}', test_dir)
del module


def parse_args(locations: Locations):
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    add_common_arguments(locations.parent_cache_dir, locations.parent_output_dir)
    return parser.parse_args()


def create_test_suite():
    test_file_strings = glob.glob('test/**/test_*.py')
    module_strings = [string.replace('/', '.').replace('.py', '') for string in test_file_strings]
    # module_strings = ['test.'+string[5:len(string)-3] for string in test_file_strings]
    suites = [unittest.defaultTestLoader.loadTestsFromName(name) for name in module_strings]
    test_suite = unittest.TestSuite(suites)
    return test_suite


if __name__ == "__main__":
    locations = g_locations
    # No need for args with unittest it defines it's own
    # args = parse_args(locations)
    # locations.
    return_code = 0
    test_suite = create_test_suite()
    text_runner = unittest.TextTestRunner().run(test_suite)
    # unittest.main()
    # Custom Tests
    # launcher = Launcher(TestRunner.get_instance())
    # return_code = 0 if launcher.run(args) else 1
    # Python unittest
    # if return_code == 0:
    #     unittest.main()
    exit(return_code)
