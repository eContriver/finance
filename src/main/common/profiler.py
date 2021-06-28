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
import os
import pstats

from main.common.fileSystem import FileSystem


class Profiler:
    """
    Is static so we can do the following anywhere in the code base...

        for i in a_list:
            Profiler.enable()
            long_running_function(i)
            Profiler.disable()
            non_profiled_function()
        Profiler.report()
    """
    instance = None
    c_profiler = None
    profile_log = ""

    def __init__(self):
        raise RuntimeError('USe get_instance() instead')

    @classmethod
    def get_instance(cls):
        if cls.instance is None:
            cls.instance = cls.__new__(cls)
            cls.instance.c_profiler = cProfile.Profile()
            script_dir = os.path.dirname(os.path.realpath(__file__))
            cache_dir = FileSystem.get_and_clean_cache_dir(os.path.join(script_dir, '..', '..', '..', '.cache', 'profiles'))
            cls.instance.profile_log = os.path.join(cache_dir, 'profile.log')
        return cls.instance

    def enable(self):
        self.c_profiler.enable()
        # logging.info(">> Profiling enabled")

    def disable_and_report(self):
        self.disable()
        self.report()

    def disable(self):
        self.c_profiler.disable()
        # logging.info(">> Profiling disabled")

    def report(self):
        logging.info(">> Profiling finished, see: {}".format(FileSystem.file_link_format(self.profile_log)))
        with open(self.profile_log, 'w') as stream:
            stats = pstats.Stats(self.c_profiler, stream=stream).sort_stats('cumtime')
            stats.print_stats()

