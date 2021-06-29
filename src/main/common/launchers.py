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
from datetime import datetime

from main.common.fileSystem import FileSystem
from main.common.profiler import Profiler


class Launcher:
    def __init__(self, runner):
        self.runner = runner
        Launcher.configure_logging()
        Launcher.print_copyright_notice()
        Launcher.check_environment()

    def run(self) -> bool:
        # Profiler.get_instance().enable()
        success = True
        run_start = datetime.now()
        runner = self.runner()
        success = success and runner.start()
        run_end = datetime.now()
        logging.info(">> Running took: {}s".format(run_end - run_start))
        if Profiler.instance is not None:  # if get_instance hasn't been called yet, then don't do the reporting
            Profiler.get_instance().disable_and_report()
        return success

    @staticmethod
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

    @staticmethod
    def print_copyright_notice():
        current_year = Launcher.get_current_copyright_year()
        original_year = 2021
        year_string = str(original_year) if current_year == original_year else f"{original_year}-{current_year}"
        logging.info(f"Finance from eContriver (C) {year_string} eContriver LLC")
        logging.info("This program comes with ABSOLUTELY NO WARRANTY; for details see the GNU GPL v3.")
        logging.info("This is free software, and you are welcome to redistribute it under certain conditions.")

    @staticmethod
    def get_current_copyright_year():
        return 2021

    @staticmethod
    def check_environment():
        if os.environ.get('DISPLAY') is None:
            raise RuntimeError(
                "The DISPLAY environment variable is not set - this is used for x11 forwarding from the docker "
                "container to the host machine for the plots.")
        else:
            logging.debug("Using display: {}".format(os.environ.get('DISPLAY')))
