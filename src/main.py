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

import logging
import os
import sys
from datetime import datetime
from os import environ

from main.common.fileSystem import FileSystem
from main.common.profiler import Profiler
from main.runners.intrinsicValueRunner import FundamentalRunner
from test.tests import test_launcher


def run_launcher():
    if environ.get('DISPLAY') is None:
        raise RuntimeError(
            "The DISPLAY environment variable is not set - this is used for x11 forwarding from the docker container "
            "to the host machine for the plots.")
    else:
        logging.debug("Using display: {}".format(environ.get('DISPLAY')))

    run_constructors = [
        # MultiSymbolRunner,
        # MatrixRunner,
        # SymbolRunner,
        # OrderRunner,
        # AlertRunner,
        FundamentalRunner,
        # MLTrainingRunner,
        # MLPredictionRunner,
    ]
    status = True
    for constructor in run_constructors:
        runner = constructor()
        # status = status and runner.start()  # will not run more upon failures
        status &= runner.start()  # will run all regardless, but final success is only true if all pass
    return status


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


if __name__ == "__main__":

    configure_logging()
    logging.info("Finance from eContriver (C) 2021 eContriver LLC")
    logging.info("This program comes with ABSOLUTELY NO WARRANTY; for details see the GNU GPL v3.")
    logging.info("This is free software, and you are welcome to redistribute it under certain conditions.")

    # Profiler.get_instance().enable()

    success = True
    test = True
    # test = False
    if test:
        test_start = datetime.now()
        success = success and test_launcher()
        test_end = datetime.now()
        logging.info(">> Testing took: {}s".format(test_end - test_start))
    run = True
    # run = False
    if run:
        run_start = datetime.now()
        success = success and run_launcher()
        run_end = datetime.now()
        logging.info(">> Running took: {}s".format(run_end - run_start))

    if Profiler.instance is not None:  # if get_instance hasn't been called yet, then don't do the reporting
        Profiler.get_instance().disable_and_report()

    exit(0 if success else 1)
