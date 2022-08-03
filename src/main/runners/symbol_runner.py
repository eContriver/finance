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

import copy
import logging
from datetime import datetime
from typing import List, Dict, Optional

from main.application.adapter import AssetType
from main.application.time_interval import TimeInterval
from main.common.locations import get_and_clean_timestamp_dir, Locations
from main.common.report import Report
from main.executors.parallel_executor import ParallelExecutor
from main.executors.parallel_strategy_executor import ParallelStrategyExecutor
from main.executors.sequential_strategy_executor import SequentialStrategyExecutor
from main.portfolio.portfolio import Portfolio
from main.application.runner import Runner, get_asset_type_overrides, get_adapter_class, NoSymbolsSpecifiedException
from main.strategies.bounded_rsi import BoundedRsi
from main.strategies.buy_and_hold import BuyAndHold
from main.strategies.buy_down_sell_up_trailing import BuyDownSellUpTrailing
from main.strategies.buy_up_sell_down_trailing import BuyUpSellDownTrailing
from main.strategies.macd_crossing import MacdCrossing
from main.strategies.soldiers_and_crows import SoldiersAndCrows
from main.strategies.strategy_type import StrategyType, add_last_bounce_strategies, add_macd_crossing_strategies, \
    add_bounded_rsi_strategies, add_buy_up_sell_down_trailing_strategies, add_buy_and_hold_strategies, \
    add_buy_down_sell_up_trailing_strategies, add_soldiers_and_crows_strategies
from main.application.strategy import Strategy
from main.visual.visualizer import Visualizer


class StrategyResultsAreEmptyException(RuntimeError):
    pass


class SymbolRunner(Runner):

    @staticmethod
    def summarize(title, strategies: List[Strategy], report: Report):
        """
        Summarizes the results of a multi-symbol run
        :param report: the report object that will be used to create the on-disk report
        :param title: The title of the run, printed as a header of the output
        :param strategies: A list of the different strategies (that were run) to report on
        """
        report.log('== {}'.format(title))
        # logging.info('== {}'.format(title))
        for strategy in strategies:
            if strategy is None:
                # logging.info("{:>100}".format("Failed to retrieve strategy data, perhaps an error occurred."))
                report.log("{:>100}".format("Failed to retrieve strategy data, perhaps an error occurred."))
            else:
                date_format: str = '%Y-%m-%d'
                start_time: Optional[datetime] = strategy.portfolio.start_time
                start_string = 'unset' if start_time is None else datetime.strftime(start_time, date_format)
                end_time: Optional[datetime] = strategy.portfolio.end_time
                end_string = 'unset' if end_time is None else datetime.strftime(end_time, date_format)
                report.log("{:>120}:  {}  ({} to {})".format(
                    # logging.info("{:>120}:  {}  ({} to {})".format(
                    # strategy.title,
                    # strategy.portfolio.title,
                    str(strategy),
                    strategy.portfolio,
                    start_string,
                    end_string))


#
# def summarize(title, strategies: List[Strategy]):
#     logging.info('== {}'.format(title))
#     for strategy in strategies:
#         logging.info("{:>90}:  {}  ({} to {})".format(strategy.title,
#                                                       strategy.portfolio,
#                                                       get_first_time(strategy),
#                                                       get_last_time(strategy)))
#

def get_first_time(strategy):
    date_format: str = '%Y-%m-%d'
    first_time = strategy.portfolio.get_first_completed_time()
    first_time = first_time if first_time is None else first_time.strftime(date_format)
    return first_time


def get_last_time(strategy):
    date_format: str = '%Y-%m-%d'
    last_time = strategy.portfolio.get_last_completed_time()
    last_time = last_time if last_time is None else last_time.strftime(date_format)
    return last_time
