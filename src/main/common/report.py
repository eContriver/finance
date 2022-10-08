# ------------------------------------------------------------------------------
#  Copyright 2021-2022 eContriver LLC
#  This file is part of Finance from eContriver.
#  -
#  Finance from eContriver is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  any later version.
#  -
#  Finance from eContriver is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  -
#  You should have received a copy of the GNU General Public License
#  along with Finance from eContriver.  If not, see <https://www.gnu.org/licenses/>.
# ------------------------------------------------------------------------------

import logging
import os
import re

import numpy


class Report:
    def __init__(self, report_path: str):
        output_dir: str = os.path.dirname(report_path)
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)
        self.file_handle = open(report_path, "w")
        self.has_closing = False
        self.closing_message = None
        self.closing_level = None

    def __del__(self):
        if self.has_closing:
            logging.log(self.closing_level, self.closing_message)
        self.file_handle.close()

    def add_closing(self, message: str, level: int = logging.INFO):
        self.has_closing = True
        self.closing_message = message
        self.closing_level = level

    def log(self, message: str, level: int = logging.INFO):
        logging.log(level, message)
        self.file_handle.write(f'{message}\n')

    @staticmethod
    def camel_to_snake(name: str):
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def to_dollars(value: float) -> str:
    abs_value = abs(value)
    if numpy.isnan(abs_value):
        value_as_str = "{}".format(value)
    elif abs_value >= 10000000000:
        value_as_str = "${:.1f}b".format(value / 1000000000)
    elif abs_value >= 10000000:
        value_as_str = "${:.1f}m".format(value / 1000000)
    elif abs_value >= 10000:
        value_as_str = "${:.1f}k".format(value / 1000)
    else:
        value_as_str = "${:.2f}".format(value)
    return value_as_str


def to_abbrev(value: float) -> str:
    abs_value = abs(value)
    if numpy.isnan(abs_value):
        value_as_str = "{}".format(value)
    elif abs_value > 10000000000:
        value_as_str = "{:.1f}b".format(value / 1000000000)
    elif abs_value > 10000000:
        value_as_str = "{:.1f}m".format(value / 1000000)
    elif abs_value > 10000:
        value_as_str = "{:.1f}k".format(value / 1000)
    else:
        value_as_str = "{:.2f}".format(value)
    return value_as_str


def to_percent(value: float) -> str:
    if numpy.isnan(value):
        value_as_str = "{}".format(value)
    else:
        value_as_str = "{:.2f}%".format(value * 100)
    return value_as_str
