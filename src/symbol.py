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

from main.application.runner import launch_runner
from main.runners.single_symbol_runner import SingleSymbolRunner


if __name__ == "__main__":
    print("DEPRECATION WARNING: Use `single_symbol.py` instead of `symbol.py` (it will be removed soon). ")
    return_code = launch_runner(program='single', config_filename='single.yaml', runner_class=SingleSymbolRunner)
    exit(return_code)
