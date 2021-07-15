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
import logging
import os.path
import pickle
import sys

import yaml

from main.common.file_system import FileSystem
from main.common.launchers import Launcher
from main.common.locations import get_and_clean_timestamp_dir
from main.common.report import Report
from main.common.shared_locations import SharedLocations
from main.runners.intrinsicValueRunner import IntrinsicValueRunner


def get_yaml_config_file_name() -> str:
    return 'intrinsic_value.yaml'


def get_input_yaml_config_path(locations: SharedLocations) -> str:
    user_dir = locations.get_parent_user_dir()
    config_path = os.path.join(user_dir, get_yaml_config_file_name())
    return config_path


def get_output_pkl_config_path(locations: SharedLocations, run_name: str) -> str:
    output_dir = locations.get_output_dir(Report.camel_to_snake(IntrinsicValueRunner.__name__))
    config_path = os.path.join(output_dir, f"{run_name}.pkl")
    return config_path


def get_output_yaml_config_path(locations: SharedLocations, run_name: str) -> str:
    output_dir = locations.get_output_dir(Report.camel_to_snake(IntrinsicValueRunner.__name__))
    config_path = os.path.join(output_dir, f"{run_name}.yaml")
    return config_path


def parse_args(default_cache_dir: str, default_output_dir: str):
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    Launcher.add_common_arguments(default_cache_dir, default_output_dir, parser)
    Launcher.add_input_config_argument(parser, get_input_yaml_config_path(locations))
    return parser.parse_args()


if __name__ == "__main__":
    locations = SharedLocations()
    args = parse_args(locations.parent_cache_dir, locations.parent_output_dir)
    locations.parent_cache_dir = args.cache_dir
    locations.parent_output_dir = args.output_dir
    # runner: IntrinsicValueRunner = read_pkl_config_file(args.config_path)
    runner = IntrinsicValueRunner()
    # read_yaml_config_file(runner, args.config_path)
    launcher = Launcher(runner)
    cache_dir = locations.get_and_clean_timestamp_dir(
    )
    return_code = 0 if launcher.run(args) else 1
    # write_pkl_config_file(runner)
    # write_yaml_config_file(runner)
    exit(return_code)
