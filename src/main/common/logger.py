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
import sys

from main.common.fileSystem import FileSystem


def configure_logging():
    logging.getLogger().setLevel(logging.DEBUG)
    out_handler = logging.StreamHandler(sys.stdout)
    out_handler.setLevel(logging.INFO)
    # out_handler.setLevel(logging.DEBUG)
    out_handler.setFormatter(logging.Formatter("%(levelname)-5s: %(message)s"))
    logging.getLogger().addHandler(out_handler)
    script_dir = os.path.dirname(os.path.realpath(__file__))
    cache_dir = FileSystem.get_and_clean_cache_dir(os.path.join(script_dir, '..', '.cache', 'runs'))
    run_log = os.path.join(cache_dir, 'run.log')
    file_handler = logging.FileHandler(run_log)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter("%(levelname)-5s: %(message)-320s %(asctime)s %(threadName)s"))
    logging.getLogger().addHandler(file_handler)
    logging.info(">> Run log: {}".format(FileSystem.file_link_format(run_log)))


def get_current_copyright_year():
    return 2021


def print_copyright_notice():
    current_year = get_current_copyright_year()
    original_year = 2021
    year_string = str(original_year) if current_year == original_year else f"{original_year}-{current_year}"
    logging.info(f"Finance from eContriver (C) {year_string} eContriver LLC")
    logging.info("This program comes with ABSOLUTELY NO WARRANTY; for details see the GNU GPL v3.")
    logging.info("This is free software, and you are welcome to redistribute it under certain conditions.")