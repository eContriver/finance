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
import os
import unittest


def load_tests(loader, standard_tests, pattern):
    # top level directory cached on loader instance
    test_dir = os.path.join(os.path.dirname(__file__), 'test')
    if pattern is None:
        package_tests = loader.discover(start_dir=test_dir)
    else:
        package_tests = loader.discover(start_dir=test_dir, pattern=pattern)
    standard_tests.addTests(package_tests)
    return standard_tests


if __name__ == "__main__":
    unittest.main()
