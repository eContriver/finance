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
from datetime import datetime

from main.common.profiler import Profiler
from main.runners.intrinsic_value_runner import IntrinsicValueRunner


def run_launcher():
    run_constructors = [
        # MultiSymbolRunner,
        # MatrixRunner,
        # SymbolRunner,
        # OrderRunner,
        # AlertRunner,
        IntrinsicValueRunner,
        # MLTrainingRunner,
        # MLPredictionRunner,
    ]
    status = True
    for constructor in run_constructors:
        runner = constructor()
        # status = status and runner.start()  # will not run more upon failures
        status &= runner.start()  # will run all regardless, but final success is only true if all pass
    return status


if __name__ == "__main__":

    configure_logging()
    print_copyright_notice()
    check_environment()

    # Profiler.get_instance().enable()

    success = True
    run_start = datetime.now()
    success = success and run_launcher()
    run_end = datetime.now()
    logging.info(">> Running took: {}s".format(run_end - run_start))

    if Profiler.instance is not None:  # if get_instance hasn't been called yet, then don't do the reporting
        Profiler.get_instance().disable_and_report()

    exit(0 if success else 1)
