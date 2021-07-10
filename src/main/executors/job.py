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
from enum import Enum
from typing import Callable, Optional


class JobLogFilter(logging.Filter):
    def __init__(self, job, *args, **kwargs):
        logging.Filter.__init__(self, *args, **kwargs)
        self.job = job

    def filter(self, record):
        return record.threadName == self.job.get_key()


class MainLogFilter(logging.Filter):
    def __init__(self, job, *args, **kwargs):
        logging.Filter.__init__(self, *args, **kwargs)
        self.job = job
        self.propagate_level = logging.WARN

    def filter(self, record):
        show_if: bool = record.levelno >= self.propagate_level
        show_if = show_if or (record.threadName != self.job.get_key())
        return show_if


class JobState(Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    PASSED = 'passed'
    FAILED = 'failed'
    EXCEPTION = 'threw exception'
    TIMEOUT = 'timeout'


class Job:
    function: Callable
    # args
    state: JobState
    exception: Optional[Exception]
    # fileHandler
    # mainFilters
    key_override: str

    def __init__(self, function, args, key_override: str = None):
        assert isinstance(function, Callable), \
            "The job function must be of Callable type, function was: {} (type: {})".format(function, type(function))
        self.function = function
        self.args = args
        self.state = JobState.PENDING
        self.exception = None
        self.file_handler = None
        self.main_filters = []
        self.key_override = key_override

    def __str__(self):
        key: str = self.get_key()
        exp_string: str = "" if self.exception is None else " - Message: {}".format(self.exception)
        return "Job {} state is {}{}".format(key, self.state.value, exp_string)

    def get_key(self):
        if self.key_override is None:
            args_string = "" if len(self.args) == 0 else "." + "_".join([str(arg) for arg in self.args])
            mod = self.function.__module__ + "." if hasattr(self.function, '__module__') else ""
            cls = self.function.__self__.__class__.__name__ + "." if hasattr(self.function, '__self__') else ""
            key = '{}{}{}{}'.format(mod, cls, self.function.__name__, args_string)
        else:
            key = self.key_override
        return key

    def get_log_file(self, log_dir):
        file_name = '{}.log'.format(self.get_key())
        keep_characters = (' ', '.', '_')
        sanitized_name = "".join(c for c in file_name if c.isalnum() or c in keep_characters).rstrip()
        log_file = os.path.join(log_dir, sanitized_name)
        return log_file

    def start_logging(self, log_dir):
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file = self.get_log_file(log_dir)
        self.file_handler = logging.FileHandler(log_file)
        self.file_handler.setLevel(logging.DEBUG)
        self.file_handler.setFormatter(
            logging.Formatter("%(levelname)-5s: %(message)-320s %(asctime)s %(threadName)s"))
        self.file_handler.addFilter(JobLogFilter(self))
        self.main_filters.append(MainLogFilter(self))
        for mainFilter in self.main_filters:
            for handler in logging.getLogger().handlers:
                handler.addFilter(mainFilter)
        logging.getLogger().addHandler(self.file_handler)

    def stop_logging(self):
        self.file_handler.close()
        logging.getLogger().removeHandler(self.file_handler)
        for mainFilter in self.main_filters:
            for handler in logging.getLogger().handlers:
                handler.removeFilter(mainFilter)
