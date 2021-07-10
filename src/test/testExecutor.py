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
import inspect
import logging
import os
from typing import List, Any

from main.common.fileSystem import FileSystem
from main.executors.job import Job
from main.executors.parallelExecutor import ParallelExecutor
from main.executors.sequentialExecutor import SequentialExecutor
from main.runners.runner import Runner


class TestRunner(Runner):
    instance = None
    only_test_specified: bool = False
    tests_to_run: List[Any] = []
    run_only_tests: List[Any] = []
    # run_gui_tests = True
    run_gui_tests = False
    ui_tests_block = False
    # ui_tests_block = True
    test_runner = None

    def __init__(self):
        super().__init__()
        raise RuntimeError('Use instance() instead')

    @classmethod
    def get_instance(cls):
        if cls.instance is None:
            cls.instance = cls.__new__(cls)
            script_dir = os.path.dirname(os.path.realpath(__file__))
            test_date_dir = FileSystem.get_and_clean_timestamp_dir(FileSystem.get_cache_dir('tests'))
            cls.instance.test_runner = TestExecutor(test_date_dir)
            # self.runTests = []
            # self.runOnlyTests = []
        return cls.instance

    def add_test_override(self, function):
        self.run_only_tests.append(function)

    def add_test(self, function):
        self.tests_to_run.append(function)

    def start(self) -> bool:
        only_test_count = len(self.run_only_tests)
        assert only_test_count <= 1, "Run only tests only accepts 1 or no tests, but found: {}".format(
            self.run_only_tests)
        test_jobs = self.run_only_tests if only_test_count == 1 else self.tests_to_run
        for run_test in test_jobs:
            self.test_runner.add_job(Job(run_test, ()))
        success = self.test_runner.start()
        return success


def only_test(function):
    TestRunner.get_instance().add_test_override(function)
    return function


def is_test(_func=None, *, should_run: bool = True):
    def decorator_is_test(function):
        if should_run:
            TestRunner.get_instance().add_test(function)
        return function

    if _func is None:
        return decorator_is_test
    else:
        return decorator_is_test(_func)


class TestExecutor(SequentialExecutor):
# class TestExecutor(ParallelExecutor):
    def __init__(self, log_dir):
        super().__init__(log_dir)

    def get_log_file(self):
        log_file = os.path.join(self.log_dir, 'test.log')
        return log_file

    def start(self) -> bool:
        success = super().start()
        logging.info(
            ' -- Testing Complete - results follow... {}'.format(FileSystem.file_link_format(self.get_log_file())))
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
