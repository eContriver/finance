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
import os

from main.common.launchers import Launcher
from main.common.locations import Locations
from main.runners.symbol_runner import SymbolRunner


def parse_args(default_cache_dir: str, default_output_dir: str, default_config_file: str):
    parser = argparse.ArgumentParser(prog='symbol', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    Launcher.add_common_arguments(parser, default_cache_dir, default_output_dir)
    Launcher.add_config_arguments(parser, default_config_file)
    return parser.parse_args()


if __name__ == "__main__":
    locations = Locations()
    input_config_path = os.path.join(locations.get_parent_user_dir(), 'symbol.yaml')
    args = parse_args(locations.parent_cache_dir, locations.parent_output_dir, input_config_path)
    locations.parent_cache_dir = args.cache_dir
    locations.parent_output_dir = args.output_dir
    input_config_path = args.config_path
    runner = SymbolRunner()
    launcher = Launcher(runner)
    return_code = 0 if launcher.run(locations, args) else 1
    exit(return_code)
