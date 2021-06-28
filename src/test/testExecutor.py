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
from typing import Optional, List

from main.common.fileSystem import FileSystem
from main.executors.parallelExecutor import ParallelExecutor
from main.executors.job import Job
from main.executors.sequentialExecutor import SequentialExecutor


# class TestExecutor(SequentialExecutor):
class TestExecutor(ParallelExecutor):
    only_test_specified: bool
    tests_to_run: List[str] = []
    run_only_tests: List[str] = []
    # run_gui_tests = True
    run_gui_tests = False
    ui_tests_block = False
    # ui_tests_block = True

    def __init__(self, log_dir):
        super().__init__(log_dir)
        self.only_test_specified = False
        # self.runTests = []
        # self.runOnlyTests = []

    @staticmethod
    def only_test(function):
        TestExecutor.run_only_tests.append(function.__name__)
        return function

    @staticmethod
    def is_test(_func=None, *, should_run: bool = True):
        def decorator_is_test(function):
            if should_run:
                TestExecutor.tests_to_run.append(function.__name__)
            return function

        if _func is None:
            return decorator_is_test
        else:
            return decorator_is_test(_func)

    def add_test(self, function, args):
        if not self.only_test_specified:
            self.add_job(Job(function, args))

    def test_only(self, function, args):
        assert not self.only_test_specified, "Test only has already been called: {}".format(self.jobs)
        if not self.only_test_specified:
            self.jobs.clear()
            self.only_test_specified = True
        self.add_job(Job(function, args))

    def get_log_file(self):
        log_file = os.path.join(self.log_dir, 'test.log')
        return log_file

    def start(self):
        success = super().start()
        logging.info(' -- Testing Complete - results follow... {}'.format(FileSystem.file_link_format(self.get_log_file())))
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
            logging.info('Tests - ALL PASSED ({}/{})'.format(passed_count, total))
        else:
            logging.error('Tests - {}/{} FAILED'.format(failed_count, total))
        return success

## The following are tests which can be used to test the ParallelTestRunner

## @test
# def test1(seconds: int):
#    logging.info('start 1:{}'.format(seconds)) 
#    logging.debug('testing pass') 
#    time.sleep(seconds)
#    logging.info('end 1') 
#    return True
#
## @test
# def test2(seconds: int):
#    logging.info('start 2:{}'.format(seconds)) 
#    logging.debug('testing fail') 
#    time.sleep(seconds)
#    logging.info('end 2') 
#    return False
#
## @test
# def test3(seconds: int):
#    logging.info('start 3:{}'.format(seconds)) 
#    logging.debug('testing exception') 
#    time.sleep(seconds)
#    logging.warn('about to throw') 
#    raise RuntimeError("Testing test exceptions")
#    logging.info('end 3') 
#    return True
