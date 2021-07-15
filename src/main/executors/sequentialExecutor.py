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
import multiprocessing
import os
import threading
import traceback
from datetime import timedelta, datetime
from typing import Any, Dict

from main.common.file_system import FileSystem
from main.executors.executor import Executor
from main.executors.job import Job, JobState


class SequentialExecutor(Executor):

    def __init__(self, log_dir):
        super(SequentialExecutor, self).__init__(log_dir)

    # @staticmethod
    # def start_process():
    #     logging.debug("Starting worker - process: {} - thread: {}".format(multiprocessing.current_process().name,
    #                                                                       threading.current_thread().name))

    @staticmethod
    def done(result):
        # logging.getLogger().flush()
        logging.debug("Result: {}".format(result))

    def add(self, function, args, key_override: str = None):
        self.jobs.append(Job(function, args, key_override))

    def add_job(self, job: Job):
        self.jobs.append(job)

    def start(self):
        self.configure_logging()
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        # pool = multiprocessing.Pool(
        #     processes=multiprocessing.cpu_count(),
        #     initializer=self.start_process
        # )
        results: Dict[Job, Any] = {}
        for job in self.jobs:
            job.state = JobState.PENDING
            results[job] = self.run_job(job)
            self.done(results[job])
            # results[job] = pool.apply_async(self.run_job, (job,), callback=self.done)
        # [result.wait() for result in results.values()]
        all_passed = self.process_results(results)
        self.restore_logging()
        return all_passed

    def process_results(self, results: Dict[Job, Any]):
        all_passed = True
        done = 0
        total = len(results)
        start_printing: datetime = datetime.now() + timedelta(seconds=10)
        for job, result in results.items():
            # is it Okay to convert the Any to a boolean here? It works for now, but maybe we should enforce it?
            job.state = JobState.PASSED if result else JobState.FAILED
            done += 1
            if datetime.now() > start_printing:
                logging.info("Complete: {}/{}".format(done, total))
            if job.state != JobState.PASSED:
                all_passed = False
        return all_passed

    def run_job(self, job: Job):
        returned = None
        try:
            # job.start_logging(self.log_dir)
            old_name = threading.current_thread().name  # logging switches with this
            threading.current_thread().name = job.get_key()  # logging switches with this
            logging.debug(
                "Starting job - process: {} - thread: {} was: {}".format(multiprocessing.current_process().name,
                                                                         threading.current_thread().name, old_name))
            job.state = JobState.RUNNING
            returned = job.function(*job.args)
            logging.debug("Job returned: {}".format(returned))
        except Exception as exception:
            logging.error("Caught exception while getting result - the job should've handled reporting of this "
                          "exception: {} (see log for debug which has stacktrace)".format(exception))
            logging.error("Exception was {}\nEXCEPTION: Caught while getting result".format(traceback.format_exc()))
            job.exception = exception
            job.state = JobState.EXCEPTION
            raise
        finally:
            # job.stop_logging()
            pass
        return returned

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
            job_log = job.get_log_file(self.log_dir)
            logging.log(level, "{} {}".format(str(job), file_link_format()))
        for job in jobs:
            if job.state == JobState.EXCEPTION:
                raise job.exception  # throw the first exception
