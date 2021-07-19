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

from main.common.launchers import Launcher
from main.runners.ml_prediction_runner import MLPredictionRunner


def parse_args():
    parser = argparse.ArgumentParser()
    Launcher.add_common_arguments(parser)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    runner = MLPredictionRunner()
    launcher = Launcher(runner)
    exit(0 if launcher.run(args) else 1)
