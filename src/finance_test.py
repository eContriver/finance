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
import importlib
import logging
import os
from datetime import datetime

from main.common.launchers import check_environment
from main.common.logger import configure_logging, print_copyright_notice
from main.common.profiler import Profiler
from test.testExecutor import TestLauncher

test_dir = 'test'
for module in os.listdir(os.path.join(os.path.dirname(__file__), test_dir)):
    if module == '__init__.py' or module[-3:] != '.py':
        continue
    importlib.import_module(f'.{module[:-3]}', test_dir)
    # __import__(module[:-3], locals(), globals())
del module


if __name__ == "__main__":

    configure_logging()
    print_copyright_notice()
    check_environment()

    # Profiler.get_instance().enable()

    success = True
    test_start = datetime.now()
    TestLauncher.instance().run()
    test_end = datetime.now()
    logging.info(">> Testing took: {}s".format(test_end - test_start))

    if Profiler.instance is not None:  # if get_instance hasn't been called yet, then don't do the reporting
        Profiler.get_instance().disable_and_report()

    exit(0 if success else 1)
