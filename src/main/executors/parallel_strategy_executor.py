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
import traceback
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from main.common.locations import file_link_format
from main.executors.job import Job, JobState
from main.executors.parallel_executor import ParallelExecutor
from main.strategies.strategy import Strategy


class StrategyJob(Job):
    group: str

    def __init__(self, function, args, group: str, key_override: str):
        super().__init__(function, args, key_override)
        self.group = group


class ParallelStrategyExecutor(ParallelExecutor):
    timeout_seconds: Optional[float]
    processed_strategies: Dict[str, List[Strategy]]

    def __init__(self, log_dir):
        super().__init__(log_dir)
        self.timeout_seconds = None
        self.processed_strategies = {}

    def add_strategy(self, function, args, group: str, key: str):
        self.add_job(StrategyJob(function, args, group, key))

    def get_log_file(self):
        log_file = os.path.join(self.log_dir, 'strategyRunner.log')
        return log_file

    def process_results(self, results):
        all_passed = True
        done = 0
        total = len(results)
        start_printing: datetime = datetime.now() + timedelta(seconds=10)
        for job, result in results.items():
            try:
                strategy: Strategy = result.get(timeout=self.timeout_seconds)
                group = job.group
                if group not in self.processed_strategies:
                    self.processed_strategies[group] = []
                self.processed_strategies[group].append(strategy)
                # expect data to be present
                job.state = JobState.PASSED if not strategy.portfolio.data.empty else JobState.FAILED
                done += 1
                if datetime.now() > start_printing:
                    logging.info("Complete: {}/{}".format(done, total))
            except multiprocessing.TimeoutError:
                logging.error(
                    "Exception was {}\nEXCEPTION: Timeout while getting job result".format(traceback.format_exc()))
                job.state = JobState.TIMEOUT
            except Exception as exception:
                logging.error("Caught exception while getting result - the job should've handled reporting of this "
                              "exception: {} (see log for debug which has stacktrace)".format(exception))
                logging.debug("Exception was {}\nEXCEPTION: Caught while getting result".format(traceback.format_exc()))
                job.exception = exception
                job.state = JobState.EXCEPTION
            if job.state != JobState.PASSED:
                all_passed = False
        return all_passed

    def start(self):
        success = super().start()
        logging.info('-- Strategies Complete - results follow... {}'.format(file_link_format(self.get_log_file())))
        (passed, failed) = self.get_results()
        passed_count = len(passed)
        failed_count = len(failed)
        if passed_count > 0:
            if failed_count > 0:
                logging.info('- Passing -')
            self.report_results(passed)
        if failed_count > 0:
            logging.info('- Failed -')
            self.report_results(failed)
        total = passed_count + failed_count
        if success:
            logging.info('Strategies - ALL PASSED ({}/{})'.format(passed_count, total))
        else:
            logging.error('Strategies - {}/{} FAILED'.format(failed_count, total))
        return success
