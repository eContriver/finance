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
import sys
from datetime import datetime
from enum import Enum, auto
from typing import List, Optional, Dict

from main.application.adapter import AssetType
from main.application.time_interval import TimeInterval
from main.common.report import Report
from main.common.locations import Locations, get_and_clean_timestamp_dir
from main.executors.parallel_strategy_executor import ParallelStrategyExecutor
from main.executors.sequential_executor import SequentialExecutor
from main.executors.sequential_strategy_executor import SequentialStrategyExecutor
from main.portfolio.portfolio import Portfolio
from main.application.runner import Runner, NoSymbolsSpecifiedException, get_adapter_class
from main.runners.symbol_runner import SymbolRunner
from main.strategies.last_bounce import LastBounce
from main.strategies.strategy_type import StrategyType, add_last_bounce_strategies, add_macd_crossing_strategies, \
    add_bounded_rsi_strategies, add_buy_up_sell_down_trailing_strategies, add_buy_and_hold_strategies, \
    add_buy_down_sell_up_trailing_strategies, add_soldiers_and_crows_strategies, add_multi_delta_swap_strategies, \
    add_multi_relative_sma_swap_up_strategies, add_multi_relative_sma_swap_dowm_strategies, add_sma_up_strategies, \
    add_testing_atr_strategies, add_testing_macd_strategies, add_testing_supertrend_strategies
from main.strategies.buy_and_hold import BuyAndHold
from main.strategies.macd_crossing import MacdCrossing
from main.strategies.multi_delta_swap import MultiDeltaSwap
from main.strategies.multi_relative_sma_swap_down import MultiRelativeSmaSwapDown
from main.strategies.multi_relative_sma_swap_up import MultiRelativeSmaSwapUp
from main.application.strategy import Strategy
from main.visual.visualizer import Visualizer


class MultiSymbolRunner(SymbolRunner):
    symbols: List[str]
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
        self.symbols = []
        self.adapter_class = None
        self.base_symbol = 'USD'
        self.graph = True
        self.parallel = True
        self.price_interval = TimeInterval.DAY
        self.start_time = None
        self.end_time = None
        self.asset_type_overrides = {}
        self.report_types = []

    # @staticmethod
    # def summarize(title, strategies: List[Strategy], report: Report):
    #     """
    #     Summarizes the results of a multi-symbol run
    #     :param report: the report object that will be used to create the on-disk report
    #     :param title: The title of the run, printed as a header of the output
    #     :param strategies: A list of the different strategies (that were run) to report on
    #     """
    #     report.log('== {}'.format(title))
    #     # logging.info('== {}'.format(title))
    #     for strategy in strategies:
    #         if strategy is None:
    #             # logging.info("{:>100}".format("Failed to retrieve strategy data, perhaps an error occurred."))
    #             report.log("{:>100}".format("Failed to retrieve strategy data, perhaps an error occurred."))
    #         else:
    #             date_format: str = '%Y-%m-%d'
    #             start_time: Optional[datetime] = strategy.portfolio.start_time
    #             start_string = 'unset' if start_time is None else datetime.strftime(start_time, date_format)
    #             end_time: Optional[datetime] = strategy.portfolio.end_time
    #             end_string = 'unset' if end_time is None else datetime.strftime(end_time, date_format)
    #             report.log("{:>120}:  {}  ({} to {})".format(
    #             # logging.info("{:>120}:  {}  ({} to {})".format(
    #                     #strategy.title,
    #                 #strategy.portfolio.title,
    #                 str(strategy),
    #                 strategy.portfolio,
    #                 start_string,
    #                 end_string))
    #
    def get_config(self) -> Dict:
        config = {
            'symbols': self.symbols,
            'adapter_class': self.adapter_class.__name__,
            'base_symbol': self.base_symbol,
            'graph': self.graph,
            'parallel': self.parallel,
            'price_interval': self.price_interval.value,
            'start_time': self.start_time,
            'end_time': self.end_time,
            # 'asset_type_overrides': asset_type_overrides, ??? TODO: needed?
            'report_types': [report_type.name for report_type in self.report_types],
        }
        return config

    def set_from_config(self, config, config_path):
        self.symbols = config['symbols']
        if not self.symbols:
            raise NoSymbolsSpecifiedException(f"Please specify at least one symbol in: {config_path}")
        self.adapter_class = get_adapter_class(config['adapter_class'])
        report_types: List[str] = config['report_types']
        self.report_types = [StrategyType[report_type] for report_type in report_types]
        if 'base_symbol' in config:
            self.base_symbol = config['base_symbol']
        if 'price_interval' in config:
            self.price_interval = TimeInterval(config['price_interval'])
        if 'graph' in config:
            self.graph = config['graph']
        if 'parallel' in config:
            self.parallel = config['parallel']
        if 'start_time' in config:
            self.start_time = datetime.combine(config['start_time'], datetime.min.time())
        if 'end_time' in config:
            self.end_time = datetime.combine(config['end_time'], datetime.min.time())
        self.check_member_variables(config_path)

    def check_member_variables(self, config_path: str):
        # validate_type('symbol', self.symbol, dict, config_path)
        if not self.symbols:
            raise NoSymbolsSpecifiedException(f"Please specify at least one symbol under 'symbol' in: "
                                              f"{config_path}")
        pass

    def get_run_name(self):
        return f"{'_'.join(sorted(self.symbols))}_{self.price_interval.value}_{self.adapter_class.__name__}"

    def start(self, locations: Locations):
        logging.info("#### Starting multi-symbol runner...")
        quantities = {}
        for symbol in self.symbols:
            quantities[symbol] = 0.0
        quantities[self.base_symbol] = 10000.0
        template: Portfolio = Portfolio('Cross Symbol Portfolio Value', quantities, self.start_time, self.end_time)
        template.interval = self.price_interval
        template.add_adapter_class(self.adapter_class)
        template.asset_type_overrides = self.asset_type_overrides
        strategy_date_dir = get_and_clean_timestamp_dir(locations.get_cache_dir('strategies'))

        # Can always run direct if things get messy...
        # MultiRelativeSmaSwapUp(self.symbols, copy.deepcopy(template), period=20, delta=1.05, look_back=10).run()
        # return True

        # Strategies
        strategies: List[Strategy] = []
        strategies += add_buy_and_hold_strategies(self.report_types, self.symbols, template)
        strategies += add_sma_up_strategies(self.report_types, self.symbols, template)
        strategies += add_testing_atr_strategies(self.report_types, self.symbols, template)
        strategies += add_testing_macd_strategies(self.report_types, self.symbols, template)
        strategies += add_testing_supertrend_strategies(self.report_types, self.symbols, template)
        strategies += add_macd_crossing_strategies(self.report_types, self.symbols, template)
        strategies += add_bounded_rsi_strategies(self.report_types, self.symbols, template)
        strategies += add_last_bounce_strategies(self.report_types, self.symbols, template)
        strategies += add_soldiers_and_crows_strategies(self.report_types, self.symbols, template)
        strategies += add_buy_up_sell_down_trailing_strategies(self.report_types, self.symbols, template)
        strategies += add_buy_down_sell_up_trailing_strategies(self.report_types, self.symbols, template)
        strategies += add_multi_delta_swap_strategies(self.report_types, self.symbols, template)
        strategies += add_multi_relative_sma_swap_up_strategies(self.report_types, self.symbols, template)
        strategies += add_multi_relative_sma_swap_dowm_strategies(self.report_types, self.symbols, template)

        key = "_".join(self.symbols)

        executor = ParallelStrategyExecutor(strategy_date_dir) if self.parallel else SequentialStrategyExecutor(
            strategy_date_dir)

        for strategy in strategies:
            executor.add_strategy(strategy.run, (), key, str(strategy).replace(' ', '_'))
        success = executor.start()
        report_on = executor.processed_strategies[key] if key in executor.processed_strategies else [None]

        output_dir = locations.get_output_dir(Report.camel_to_snake(self.__class__.__name__))
        report_name = f"{self.get_run_name()}.md"
        report_path = os.path.join(output_dir, report_name)
        report: Report = Report(report_path)
        report.log("```")
        report.add_closing("```")

        title = f'Multi-Symbol Runner - Strategy Comparison {self.symbols}'
        self.summarize(title, report_on, report)

        if self.graph:
            visual_date_dir = get_and_clean_timestamp_dir(locations.get_output_dir('visuals'))
            visual_runner = SequentialExecutor(visual_date_dir)
            # visual_runner = ParallelExecutor(visual_date_dir)
            for strategy in executor.processed_strategies[key]:
                if strategy is None:
                    logging.warning("Encountered a '{}' strategy, it will not be graphed.".format(strategy))
                    continue
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
