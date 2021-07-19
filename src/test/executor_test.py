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

from main.common.locations import file_link_format
from main.executors.parallel_executor import ParallelExecutor


# class TestExecutor(SequentialExecutor):
class TestExecutor(ParallelExecutor):
    def __init__(self, log_dir):
        super().__init__(log_dir)

    def get_log_file(self):
        log_file = os.path.join(self.log_dir, 'test.log')
        return log_file

    def start(self) -> bool:
        success = super().start()
        logging.info(
            ' -- Testing Complete - results follow... {}'.format(file_link_format(self.get_log_file())))
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
