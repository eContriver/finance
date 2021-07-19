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
import sys
from typing import List, Any, Dict, Optional

from main.common.locations import Locations, get_and_clean_timestamp_dir
from main.common.report import Report
from main.executors.job import Job
from main.executors.parallel_executor import ParallelExecutor
from main.executors.sequential_executor import SequentialExecutor
from main.runners.intrinsic_value_runner import validate_type
from main.runners.runner import Runner
from test.executor_test import TestExecutor


class UnknownExecutorException(RuntimeError):
    pass


class AlreadySetMemberVariableException(RuntimeError):
    pass


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
    def get_instance(cls, test_date_dir: Optional[str] = None):
        if test_date_dir and cls.instance:
            raise AlreadySetMemberVariableException(f"The get_instance must only be called the first time with test date dir set, it was called again with new valid: '{test_date_dir}'")
        if cls.instance is None:
            cls.instance = cls.__new__(cls)
            # script_dir = os.path.dirname(os.path.realpath(__file__))
            # test_date_dir = get_and_clean_timestamp_dir(locations.get_cache_dir('test'))
            # location =
            cls.instance.test_runner = TestExecutor(test_date_dir)
            # self.runTests = []
            # self.runOnlyTests = []
        return cls.instance

    def get_config(self) -> Dict:
        config = {
            'executor_class': self.executor_class.__name__,
            'graph': self.graph,
        }
        return config

    def set_from_config(self, config, config_path):
        class_name = config['executor_class']
        self.executor_class = getattr(
            sys.modules[f'main.adapters.third_party_shims.{Report.camel_to_snake(class_name)}'], f'{class_name}')
        self.graph = config['graph']
        self.check_member_variables(config_path)

    def check_member_variables(self, config_path: str):
        validate_type('graph', self.graph, bool, config_path)
        # WARNING: This check is also responsible for the includes in this file so that the Executors are imported
        allowed_executors = [
            ParallelExecutor.__name__,
            SequentialExecutor.__name__
        ]
        if self.executor_class in allowed_executors:
            raise UnknownExecutorException(f"Received '{self.executor_class}' please specify "
                                           f"one of: {allowed_executors}")

    def get_run_name(self):
        return f"{self.executor_class.__name__}"

    def add_test_override(self, function):
        self.run_only_tests.append(function)

    def add_test(self, function):
        self.tests_to_run.append(function)

    def start(self, locations: Locations) -> bool:
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