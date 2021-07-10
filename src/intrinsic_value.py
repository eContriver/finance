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
import os.path

from main.common.fileSystem import FileSystem
from main.common.launchers import Launcher
from main.runners.intrinsicValueRunner import IntrinsicValueRunner


def parse_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    Launcher.add_default_arguments(parser)
    user_dir = FileSystem.get_parent_user_dir()  # Set in add_default_arguments
    config_path = os.path.join(user_dir, 'intrinsic_value.yaml')
    parser.add_argument("-i", "--input-config", dest='config_path', type=str, default=config_path,
                        help=f"Read config file from the specified location")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    FileSystem.parent_cache_dir = args.cache_dir
    FileSystem.parent_output_dir = args.output_dir
    runner = IntrinsicValueRunner(args.config_path)
    launcher = Launcher(runner)
    exit(0 if launcher.run(args) else 1)
