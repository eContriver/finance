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
import datetime
import logging
import sys
from typing import List, Optional, Dict

from main.adapters.adapter import TimeInterval, AssetType
from main.common.profiler import Profiler
from main.common.report import Report
from main.common.locations import Locations, get_and_clean_timestamp_dir
from main.executors.parallel_executor import ParallelExecutor
from main.executors.parallel_strategy_executor import ParallelStrategyExecutor
from main.executors.sequential_executor import SequentialExecutor
from main.executors.sequential_strategy_executor import SequentialStrategyExecutor
from main.portfolio.portfolio import Portfolio
from main.runners.runner import Runner, NoSymbolsSpecifiedException
from main.strategies.buy_and_hold import BuyAndHold
from main.strategies.multi_delta_swap import MultiDeltaSwap
from main.strategies.multi_relative_sma_swap_down import MultiRelativeSmaSwapDown
from main.strategies.multi_relative_sma_swap_up import MultiRelativeSmaSwapUp
from main.strategies.strategy import Strategy
from main.visual.visualizer import Visualizer


class MultiSymbolRunner(Runner):
    symbols: List[str]
    adapter_class: Optional[type]
    base_symbol: str
    graph: bool
    price_interval: TimeInterval

    def __init__(self):
        super().__init__()
        self.symbols = []
        self.adapter_class = None
        self.base_symbol = 'USD'
        self.graph = True
        self.price_interval = TimeInterval.DAY

    @staticmethod
    def summarize(title, strategies: List[Strategy]):
        """
        Summarizes the results of a multi-symbol run
        :param title: The title of the run, printed as a header of the output
        :param strategies: A list of the different strategies (that were run) to report on
        """
        logging.info('== {}'.format(title))
        for strategy in strategies:
            if strategy is None:
                logging.info("{:>60}".format("Failed to retrieve strategy data, perhaps an error occurred."))
            else:
                logging.info("{:>60}:  {}  ({} to {})".format(strategy.title,  # str(strategy)
                                                              strategy.portfolio,
                                                              strategy.portfolio.start_time,
                                                              strategy.portfolio.end_time))

    def get_config(self) -> Dict:
        config = {
            'adapter_class': self.adapter_class.__name__,
            'base_symbol': self.base_symbol,
            'symbols': self.symbols,
            'graph': self.graph,
            'price_interval': self.price_interval.value,
        }
        return config

    def set_from_config(self, config, config_path):
        self.symbols = config['symbols']
        if not self.symbols:
            raise NoSymbolsSpecifiedException(f"Please specify at least one symbol in: {config_path}")
        class_name = config['adapter_class']
        self.adapter_class = getattr(
            sys.modules[f'main.adapters.third_party_adapters.{Report.camel_to_snake(class_name)}'], f'{class_name}')
        self.base_symbol = config['base_symbol']
        self.price_interval = TimeInterval(config['price_interval'])
        self.graph = config['graph']

    def get_run_name(self):
        return f"{'_'.join(sorted(self.symbols))}_{self.price_interval.value}_{self.adapter_class.__name__}"

    def start(self, locations: Locations):
        logging.info("#### Starting multi-symbol runner...")
        # SymbolCollection
        # self.symbols = ['ETH', 'BTC']
        # Sector Analysis
        # https://discord.com/channels/584088953788039174/780316832531873844/864730112104595467
        # self.symbols = [
        #     # 'XLF',
        #     'XLK',
        #     # 'XLI',
        #     # 'XLB',
        #     # 'XLV',
        #     # 'XLU',
        #     'XLE',
        #     # 'XLP',
        #     # 'XLY'
        # ]
        # Portfolio
        start_time = None
        end_time = None
        # end_time = datetime(2010, 1, 1)
        quantities = {}
        for symbol in self.symbols:
            quantities[symbol] = 0.0
        # quantities['ETH'] = 10.0
        quantities[self.base_symbol] = 10000.0
        template: Portfolio = Portfolio('Cross Symbol Portfolio Value', quantities, start_time, end_time)
        # template.start_time = datetime.datetime(year=2021, month=1, day=1)
        template.interval = self.price_interval
        template.add_adapter_class(self.adapter_class)
        template.asset_type_overrides = {
            'ETH': AssetType.DIGITAL_CURRENCY,
            'LTC': AssetType.DIGITAL_CURRENCY
        }

        strategy_date_dir = get_and_clean_timestamp_dir(locations.get_cache_dir('strategy'))

        # Can always run direct if things get messy...
        # MultiRelativeSmaSwapUp(self.symbols, copy.deepcopy(template), period=20, delta=1.05, look_back=10).run()
        # return True

        # Strategies
        strategies: List[Strategy] = []
        for symbol in self.symbols:
            # strategies.append(BuyAndHold(symbol, copy.deepcopy(template)))
            pass

        deltas = [
            1.1,
            # 1.05,
            # 1.025,
        ]
        for delta in deltas:
            # strategies.append(MultiDeltaSwap(self.symbols, copy.deepcopy(template), delta=delta))
            pass

        deltas = [
            # 0.8, 0.9,
            # 0.95, 0.975,
            1.0,
            # 1.05, 1.025,
            # 1.2, 1.1,
        ]
        look_backs = [
            # 5, 10, 15,
            20,
            # 25, 30, 35
        ]
        periods = [20]
        for period in periods:
            for delta in deltas:
                for look_back in look_backs:
                    strategies.append(
                        MultiRelativeSmaSwapUp(self.symbols, copy.deepcopy(template), period, delta, look_back))
                    # strategies.append(
                    #     MultiRelativeSmaSwapDown(self.symbols, copy.deepcopy(template), period, delta, look_back))
                    pass

        key = "_".join(self.symbols)
        executor = SequentialStrategyExecutor(strategy_date_dir)
        # strategy_runner = ParallelStrategyExecutor(strategy_date_dir)
        for strategy in strategies:
            executor.add_strategy(strategy.run, (), key, str(strategy).replace(' ', '_'))
        success = executor.start()
        report_on = executor.processed_strategies[key] if key in executor.processed_strategies else [None]

        title = 'Multi-Symbol Runner - Strategy Comparison {}'.format(
            self.symbols)  # - {} - {} to {}'.format(symbol, start_time, end_time)
        self.summarize(title, report_on)

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
