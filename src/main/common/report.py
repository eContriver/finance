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

import logging
import os
import re


class Report:
    def __init__(self, report_path: str):
        output_dir: str = os.path.dirname(report_path)
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)
        self.file_handle = open(report_path, "w")

    def __del__(self):
        self.file_handle.close()

    def log(self, message: str, level: int = logging.INFO):
        logging.log(level, message)
        self.file_handle.write(f'{message}\n')

    @staticmethod
    def camel_to_snake(name: str):
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

