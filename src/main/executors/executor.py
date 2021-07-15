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
import shutil
import sys

from main.common.file_system import FileSystem
from main.executors.job import Job, JobState


class Executor:
    logging_level = None
    logging_handlers = []

    def __init__(self, log_dir):
        self.jobs: list[Job] = []
        self.log_dir = log_dir
        # self.timeout_seconds: int = 30  # WARNING: This is the time from one result check to the not total job time

    def configure_logging(self):
        self.logging_level = logging.getLogger().level
        for handler in logging.getLogger().handlers:
            self.logging_handlers.append(handler)
        for handler in self.logging_handlers:  # do not remove in logging.getLogger().handlers loop
            logging.getLogger().removeHandler(handler)
        # Global reporting level
        logging.getLogger().setLevel(logging.DEBUG)
        # STDOUT
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.INFO)
        console.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
        logging.getLogger().addHandler(console)
        # Log File
        if os.path.exists(self.log_dir):
            shutil.rmtree(self.log_dir)
        os.makedirs(self.log_dir)
        file_handler = logging.FileHandler(self.get_log_file())
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter("%(levelname)-5s %(message)-320s %(asctime)s %(threadName)s"))
        logging.getLogger().addHandler(file_handler)

    def get_log_file(self):
        log_file = os.path.join(self.log_dir, 'runner.log')
        return log_file

    def restore_logging(self) -> None:
        handlers = list(logging.getLogger().handlers)  # copy so list doesn't change under us
        for handler in handlers:
            logging.getLogger().removeHandler(handler)
        assert not logging.getLogger().hasHandlers()
        for handler in self.logging_handlers:
            logging.getLogger().addHandler(handler)
        if self.logging_level is not None:
            logging.getLogger().setLevel(self.logging_level)

    def run_job(self, job: Job):
        raise NotImplementedError("This method is intended to be overrode (this is an abstract method)")

    def get_results(self):
        passed = []
        failed = []
        for job in self.jobs:
            if job.state == JobState.PASSED:
                passed.append(job)
            else:
                failed.append(job)
        return passed, failed

    def report_results(self, jobs):
        for job in jobs:
            level = logging.INFO if (job.state == JobState.PASSED) else logging.ERROR
            log_file = job.get_log_file(self.log_dir)
            logging.log(level, "{} {}".format(str(job), file_link_format()))

#     def __init__(self, log_dir):
#         self.jobs: list[Job] = []
#         self.log_dir = log_dir
#         self.timeout_seconds: int = 30  # WARNING: This is the time from one result check to the not total job time
#
#     @staticmethod
#     def start_process():
#         logging.debug("Starting worker - process: {} - thread: {}".format(multiprocessing.current_process().name,
#                                                                           threading.current_thread().name))
#
#     @staticmethod
#     def done(result):
#         # logging.getLogger().flush()
#         logging.debug("Result: {}".format(result))
#
#     def add(self, function, args, key_override: str = None):
#         self.jobs.append(Job(function, args, key_override))
#
#     def add_job(self, job: Job):
#         self.jobs.append(job)
#
#     def start(self):
#         self.configure_logging()
#         if not os.path.exists(self.log_dir):
#             os.makedirs(self.log_dir)
#         pool = multiprocessing.Pool(
#             processes=multiprocessing.cpu_count(),
#             initializer=self.start_process
#         )
#         results = {}
#         for job in self.jobs:
#             job.state = JobState.PENDING
#             results[job] = pool.apply_async(self.run_job, (job,), callback=self.done)
#         [result.wait() for result in results.values()]
#         all_passed = self.process_results(results)
#         self.restore_logging()
#         return all_passed
#
#     def configure_logging(self):
#         self.logging_level = logging.getLogger().level
#         for handler in logging.getLogger().handlers:
#             self.logging_handlers.append(handler)
#         for handler in self.logging_handlers:  # do not remove in logging.getLogger().handlers loop
#             logging.getLogger().removeHandler(handler)
#         # Global reporting level
#         logging.getLogger().setLevel(logging.DEBUG)
#         # STDOUT
#         console = logging.StreamHandler(sys.stdout)
#         console.setLevel(logging.INFO)
#         console.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
#         logging.getLogger().addHandler(console)
#         # Log File
#         if os.path.exists(self.log_dir):
#             shutil.rmtree(self.log_dir)
#         os.makedirs(self.log_dir)
#         file_handler = logging.FileHandler(self.get_log_file())
#         file_handler.setLevel(logging.DEBUG)
#         file_handler.setFormatter(logging.Formatter("%(levelname)-5s %(message)-320s %(asctime)s %(threadName)s"))
#         logging.getLogger().addHandler(file_handler)
#
#     def get_log_file(self):
#         log_file = os.path.join(self.log_dir, 'runner.log')
#         return log_file
#
#     def restore_logging(self) -> None:
#         handlers = list(logging.getLogger().handlers)  # copy so list doesn't change under us
#         for handler in handlers:
#             logging.getLogger().removeHandler(handler)
#         assert not logging.getLogger().hasHandlers()
#         for handler in self.logging_handlers:
#             logging.getLogger().addHandler(handler)
#         if self.logging_level is not None:
#             logging.getLogger().setLevel(self.logging_level)
#
#     def process_results(self, results):
#         all_passed = True
#         done = 0
#         total = len(results)
#         start_printing: datetime = datetime.now() + timedelta(seconds=10)
#         for job, result in results.items():
#             try:
#                 job.state = JobState.PASSED if result.get(timeout=self.timeout_seconds) else JobState.FAILED
#                 done += 1
#                 if datetime.now() > start_printing:
#                     logging.info("Complete: {}/{}".format(done, total))
#             except multiprocessing.TimeoutError:
#                 logging.error(
#                     "Exception was {}\nEXCEPTION: Timeout while getting job result".format(traceback.format_exc()))
#                 job.state = JobState.TIMEOUT
#             except Exception as exception:
#                 logging.error("Caught exception while getting result - the job should've handled reporting of this "
#                               "exception: {} (see log for debug which has stacktrace)".format(exception))
#                 logging.debug("Exception was {}\nEXCEPTION: Caught while getting result".format(traceback.format_exc()))
#                 job.exception = exception
#                 job.state = JobState.EXCEPTION
#             if job.state != JobState.PASSED:
#                 all_passed = False
#         return all_passed
#
#     def run_job(self, job: Job):
#         try:
#             job.start_logging(self.log_dir)
#             old_name = threading.current_thread().name  # logging switches with this
#             threading.current_thread().name = job.get_key()  # logging switches with this
#             logging.debug(
#                 "Starting job - process: {} - thread: {} was: {}".format(multiprocessing.current_process().name,
#                                                                          threading.current_thread().name, old_name))
#             job.state = JobState.RUNNING
#             returned = job.function(*job.args)
#             logging.debug("Job returned: {}".format(returned))
#         except Exception:
#             logging.error("Exception was {}\nEXCEPTION: Caught while running job".format(traceback.format_exc()))
#             raise
#         finally:
#             job.stop_logging()
#         return returned
#
#     def get_results(self):
#         passed = []
#         failed = []
#         for job in self.jobs:
#             if job.state == JobState.PASSED:
#                 passed.append(job)
#             else:
#                 failed.append(job)
#         return passed, failed
#
#     def report_results(self, jobs):
#         for job in jobs:
#             level = logging.INFO if (job.state == JobState.PASSED) else logging.ERROR
#             logging.log(level, "{} file://{}".format(str(job), job.get_log_file(self.log_dir)))
