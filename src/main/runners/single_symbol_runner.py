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
import os
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
from main.runners.symbol_runner import SymbolRunner
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


class SingleSymbolRunner(SymbolRunner):
    symbol: Optional[str]
    adapter_class: Optional[type]
    base_symbol: str
    graph: bool
    parallel: bool
    price_interval: TimeInterval
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    asset_type_overrides: Dict[str, AssetType]
    report_types: List[StrategyType]

    def __init__(self):
        super().__init__()
        self.symbol = None
        self.adapter_class = None
        self.base_symbol = 'USD'
        self.graph = False
        self.parallel = True
        self.price_interval = TimeInterval.DAY
        self.start_time = None
        self.end_time = None
        self.asset_type_overrides = {}
        self.report_types = []

    def get_config(self) -> Dict:
        asset_type_overrides = {}
        for symbol, asset_type in self.asset_type_overrides.items():
            asset_type_overrides[self.symbol] = asset_type.name
        config = {
            'symbol': self.symbol,
            'adapter_class': self.adapter_class.__name__,
            'base_symbol': self.base_symbol,
            'graph': self.graph,
            'parallel': self.parallel,
            'price_interval': self.price_interval.value,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'asset_type_overrides': asset_type_overrides,
            'report_types': [report_type.name for report_type in self.report_types],
        }
        return config

    def set_from_config(self, config, config_path):
        self.symbol = config['symbol']
        self.adapter_class = get_adapter_class(config['adapter_class'])
        report_types: List[str] = config['report_types']
        self.report_types = [StrategyType[report_type] for report_type in report_types]
        if 'asset_type_overrides' in config:
            self.asset_type_overrides = get_asset_type_overrides(config['asset_type_overrides'])
        if 'graph' in config:
            self.graph = config['graph']
        if 'parallel' in config:
            self.parallel = config['parallel']
        if 'base_symbol' in config:
            self.base_symbol = config['base_symbol']
        if 'price_interval' in config:
            self.price_interval = TimeInterval(config['price_interval'])
        if 'start_time' in config:
            self.start_time = datetime.combine(config['start_time'], datetime.min.time())
        if 'end_time' in config:
            self.end_time = datetime.combine(config['end_time'], datetime.min.time())
        self.check_member_variables(config_path)

    def check_member_variables(self, config_path: str):
        # validate_type('symbol', self.symbol, dict, config_path)
        if not self.symbol:
            raise NoSymbolsSpecifiedException(f"Please specify at least one symbol under 'symbol' in: "
                                              f"{config_path}")
        pass

    def get_run_name(self):
        return "SymbolRun"
        # return f"{self.price_interval.value.title()}_{self.adapter_class.__name__}"

    def start(self, locations: Locations):
        logging.info("#### Starting symbol runner...")

        # start_time = None
        # start_time = datetime.now() - (1 * TimeInterval.YEAR.timedelta)
        # end_time = None
        end_time: datetime = self.end_time if self.end_time else datetime.now()
        # end_time = datetime(2010, 1, 1)
        template: Portfolio = Portfolio('Single Symbol Portfolio Value', {'USD': 20000.0, self.symbol: 0.0},
                                        self.start_time, end_time)
        # template.interval = TimeInterval.DAY
        template.interval = TimeInterval.WEEK
        template.add_adapter_class(self.adapter_class)
        template.asset_type_overrides = self.asset_type_overrides

        # script_dir = os.path.dirname(os.path.realpath(__file__))
        strategy_date_dir = get_and_clean_timestamp_dir(locations.get_cache_dir('strategies'))

        # Strategies
        strategies: List[Strategy] = []
        strategies += add_buy_and_hold_strategies(self.report_types, [self.symbol], template)
        strategies += add_macd_crossing_strategies(self.report_types, [self.symbol], template)
        strategies += add_bounded_rsi_strategies(self.report_types, [self.symbol], template)
        strategies += add_last_bounce_strategies(self.report_types, [self.symbol], template)
        strategies += add_soldiers_and_crows_strategies(self.report_types, [self.symbol], template)
        strategies += add_buy_up_sell_down_trailing_strategies(self.report_types, [self.symbol], template)
        strategies += add_buy_down_sell_up_trailing_strategies(self.report_types, [self.symbol], template)
        # strategies.append(BookDepth(self.symbol, copy.deepcopy(template), period=14.0))

        # success = True
        # for strategy in strategies:
        #     strategy.run()
        # report_on = strategies

        strategy_runner = ParallelStrategyExecutor(strategy_date_dir) if self.parallel else SequentialStrategyExecutor(strategy_date_dir)

        for strategy in strategies:
            # whitelist = [MacdCrossing]
            whitelist = []
            if len(whitelist) > 0 and strategy.__class__ not in whitelist:
                continue
            key = str(strategy).replace(' ', '_')
            strategy_runner.add_strategy(strategy.run, (), self.symbol, key)
        success = strategy_runner.start()
        if self.symbol not in strategy_runner.processed_strategies:
            raise
        report_on = strategy_runner.processed_strategies[self.symbol]

        output_dir = locations.get_output_dir(Report.camel_to_snake(self.__class__.__name__))
        report_name = f"{self.get_run_name()}.md"
        report_path = os.path.join(output_dir, report_name)
        report: Report = Report(report_path)
        report.log("```")
        report.add_closing("```")

        title = 'Symbol Runner - Strategy Comparison {}'.format(
            self.symbol)  # - {} - {} to {}'.format(self.symbol, start_time, end_time)
        self.summarize(title, report_on, report)
        # summarize(title, report_on)

        # call directly
        # for strategy in report_on:
        #     visualizer: Visualizer = Visualizer(str(strategy), strategy.collection, [strategy.portfolio])
        #     visualizer.plot_all()

        if self.graph:
            visual_date_dir = get_and_clean_timestamp_dir(locations.get_cache_dir('visualizer'))
            # visual_runner = SequentialExecutor(visual_date_dir)
            visual_runner = ParallelExecutor(visual_date_dir)
            for strategy in report_on:
                visualizer: Visualizer = Visualizer(str(strategy), strategy.collection, [strategy.portfolio])
                # visualizer.annotate_canceled_orders = True
                # visualizer.annotate_opened_orders = True
                # visualizer.annotate_open_prices = True
                # visualizer.annotate_close_prices = True
                # visualizer.draw_high_prices = False
                # visualizer.draw_low_prices = False
                # visualizer.draw_open_prices = True
                # visualizer.draw_close_prices = True
                visual_runner.add(visualizer.plot_all, (), str(strategy).replace(' ', '_'))
            visual_runner.start()

        # drawn: int = 0
        # count: int = len(processed_strategies)
        # for strategy in processed_strategies:
        #     drawn += 1
        #     visualizer: Visualizer = Visualizer(strategy.title, strategy.collection, [strategy.portfolio])
        #     visualizer.plot_all(drawn >= count)

        return success


def summarize(title, strategies: List[Strategy]):
    logging.info('== {}'.format(title))
    for strategy in strategies:
        logging.info("{:>90}:  {}  ({} to {})".format(strategy.title,
                                                      strategy.portfolio,
                                                      get_first_time(strategy),
                                                      get_last_time(strategy)))


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
