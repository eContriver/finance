#!/usr/local/bin/python

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
import importlib
import os

from main.common.launchers import Launcher
from test.testExecutor import TestRunner

# NOTE: This code automatically adds all modules in the test directory
test_dir = 'test'
for module in os.listdir(os.path.join(os.path.dirname(__file__), test_dir)):
    if module == '__init__.py' or module[-3:] != '.py':
        continue
    importlib.import_module(f'.{module[:-3]}', test_dir)
del module


def parse_args():
    parser = argparse.ArgumentParser()
    Launcher.add_default_arguments(parser)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    launcher = Launcher(TestRunner.get_instance())
    exit(0 if launcher.run(args) else 1)
