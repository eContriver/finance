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
import os.path
from typing import List

from main.adapters.adapter import TimeInterval, AssetType
from main.adapters.third_party_shims.alpha_vantage import AlphaVantage
from main.common.file_system import FileSystem
from main.executors.parallelExecutor import ParallelExecutor
from main.executors.parallelStrategyExecutor import ParallelStrategyExecutor
from main.portfolio.portfolio import Portfolio
from main.runners.runner import Runner
from main.strategies.buyAndHold import BuyAndHold
from main.strategies.multiRelativeSmaSwapDown import MultiRelativeSmaSwapDown
from main.strategies.multiRelativeSmaSwapUp import MultiRelativeSmaSwapUp
from main.strategies.strategy import Strategy
from main.visual.visualizer import Visualizer


class MultiSymbolRunner(Runner):
    def __init__(self):
        super().__init__()

    @staticmethod
    def summarize(title, strategies: List[Strategy]):
        logging.info('== {}'.format(title))
        for strategy in strategies:
            if strategy is None:
                logging.info("{:>60}".format("Failed to retrieve strategy data, perhaps an error occurred."))
            else:
                logging.info("{:>60}:  {}  ({} to {})".format(str(strategy),  # .title,
                                                              strategy.portfolio,
                                                              strategy.portfolio.start_time,
                                                              strategy.portfolio.end_time))

    def start(self):
        logging.info("#### Starting multi-symbol runner...")

        # SymbolCollection
        # symbols = ['ETH', 'BTC']
        # Sector Analysis
        # https://discord.com/channels/584088953788039174/780316832531873844/864730112104595467
        symbols = [
            # 'XLF',
            'XLK',
            # 'XLI',
            # 'XLB',
            # 'XLV',
            # 'XLU',
            'XLE',
            # 'XLP',
            # 'XLY'
        ]
        # Portfolio
        start_time = None
        end_time = None
        # end_time = datetime(2010, 1, 1)
        quantities = {}
        for symbol in symbols:
            quantities[symbol] = 0.0
        # quantities['ETH'] = 10.0
        quantities['USD'] = 10000.0
        template: Portfolio = Portfolio('Cross Symbol Portfolio Value', quantities, start_time, end_time)
        template.interval = TimeInterval.DAY
        template.add_adapter_class(AlphaVantage)
        template.asset_type_overrides = {
            'ETH': AssetType.DIGITAL_CURRENCY,
            'LTC': AssetType.DIGITAL_CURRENCY
        }

        script_dir = os.path.dirname(os.path.realpath(__file__))
        strategy_date_dir = get_and_clean_timestamp_dir()

        # Can always run direct if things get messy...
        # MultiRelativeSmaSwapUp(symbols, copy.deepcopy(template), period=20, delta=1.05, look_back=10).run()
        # return True

        # Strategies
        strategies: List[Strategy] = []
        for symbol in symbols:
            strategies.append(BuyAndHold(symbol, copy.deepcopy(template)))
            pass

        deltas = [
            1.1,
            1.05,
            1.025,
        ]
        for delta in deltas:
            # strategies.append(MultiDeltaSwap(symbols, copy.deepcopy(template), delta=delta))
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
                        MultiRelativeSmaSwapUp(symbols, copy.deepcopy(template), period, delta, look_back))
                    strategies.append(
                        MultiRelativeSmaSwapDown(symbols, copy.deepcopy(template), period, delta, look_back))
                    pass

        key = "_".join(symbols)
        # strategy_runner = SequentialStrategyExecutor(strategy_date_dir)
        strategy_runner = ParallelStrategyExecutor(strategy_date_dir)
        for strategy in strategies:
            strategy_runner.add_strategy(strategy.run, (), key, str(strategy).replace(' ', '_'))
        success = strategy_runner.start()
        report_on = strategy_runner.processed_strategies[key] if key in strategy_runner.processed_strategies else [None]

        title = 'Multi-Symbol Runner - Strategy Comparison {}'.format(
            symbols)  # - {} - {} to {}'.format(symbol, start_time, end_time)
        self.summarize(title, report_on)

        draw = True
        # draw = False
        if draw:
            visual_date_dir = get_and_clean_timestamp_dir()
            # visual_runner = SequentialExecutor(visual_date_dir)
            visual_runner = ParallelExecutor(visual_date_dir)
            for strategy in strategy_runner.processed_strategies[key]:
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
