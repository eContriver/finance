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

from datetime import datetime

from main.common.launchers import Launcher
from test.runner_test import is_test


@is_test
# @only_test
def check_copyright_year():
    now = datetime.now()
    copyright_year = Launcher.get_current_copyright_year()
    assert now.year == copyright_year, f"Current year is '{now.year}' and copyright year is '{copyright_year}'. When " \
                                       f"tests run, it is assumed that code will be changing and as such copyright " \
                                       f"notices should also be updated, but they currently are out-of-date."
    return True