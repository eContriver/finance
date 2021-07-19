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

import cProfile
import logging
import pstats

from main.common.locations import file_link_format


class Profiler:
    """
    Is singleton so we can do the following anywhere in the code base...

        for i in a_list:
            Profiler.enable()
            long_running_function(i)
            Profiler.disable()
            non_profiled_function()
        Profiler.report()
    """
    instance = None
    c_profiler = None

    def __init__(self):
        raise RuntimeError('Use get_instance() instead')

    @classmethod
    def get_instance(cls):
        if cls.instance is None:
            cls.instance = cls.__new__(cls)
            cls.instance.c_profiler = cProfile.Profile()
        return cls.instance

    def enable(self, echo: bool = True):
        if echo:
            logging.info(">> Profiling enabled")
        self.c_profiler.enable()

    def disable_and_report(self, profile_log: str):
        self.disable()
        self.report(profile_log)

    def disable(self, echo: bool = True):
        self.c_profiler.disable()
        if echo:
            logging.info(">> Profiling disabled")

    def report(self, profile_log: str):
        logging.info(">> Profiling finished, see: {}".format(file_link_format(profile_log)))
        with open(profile_log, 'w') as stream:
            stats = pstats.Stats(self.c_profiler, stream=stream).sort_stats('cumtime')
            stats.print_stats()

