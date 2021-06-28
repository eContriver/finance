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
from datetime import datetime
from typing import List

from main.adapters.adapter import TimeInterval, AssetType
from main.adapters.thirdPartyShims.alphaVantage import AlphaVantage
from main.adapters.thirdPartyShims.iexCloud import IexCloud
from main.common.fileSystem import FileSystem
from main.executors.parallelExecutor import ParallelExecutor
from main.executors.parallelStrategyExecutor import ParallelStrategyExecutor
from main.executors.sequentialExecutor import SequentialExecutor
from main.executors.sequentialStrategyExecutor import SequentialStrategyExecutor
from main.portfolio.portfolio import Portfolio
from main.runners.runner import Runner
from main.strategies.boundedRsi import BoundedRsi
from main.strategies.buyAndHold import BuyAndHold
from main.strategies.buyDownSellUpTrailing import BuyDownSellUpTrailing
from main.strategies.buyUpSellDownTrailing import BuyUpSellDownTrailing
from main.strategies.lastBounce import LastBounce
from main.strategies.macdCrossing import MacdCrossing
from main.strategies.soldiersAndCrows import SoldiersAndCrows
from main.strategies.strategy import Strategy
from main.visual.visualizer import Visualizer


class SymbolRunner(Runner):
    def __init__(self):
        super().__init__()

    @staticmethod
    def summarize(title, strategies: List[Strategy]):
        logging.info('== {}'.format(title))
        for strategy in strategies:
            logging.info("{:>90}:  {}  ({} to {})".format(strategy.title,
                                                          strategy.portfolio,
                                                          strategy.portfolio.start_time,
                                                          strategy.portfolio.end_time))

    def start(self):
        logging.info("#### Starting symbol runner...")

        # SymbolCollection
        symbol = 'AAPL'
        # symbol = 'BTC'
        # Portfolio
        start_time = None
        # start_time = datetime.now() - (2 * TimeInterval.YEAR.timedelta)
        end_time = None
        # end_time = datetime(2010, 1, 1)
        template: Portfolio = Portfolio('Single Symbol Portfolio Value', {'USD': 20000.0, symbol: 0.0},
                                        start_time, end_time)
        # template.interval = TimeInterval.DAY
        template.interval = TimeInterval.WEEK
        # template.add_data_adapter_class(IexCloud)
        # template.add_data_adapter_class(CoinbaseProAdapter)
        # template.add_data_adapter_class(Quandl)
        # template.add_data_adapter_class(FinancialModelingPrep)
        template.add_adapter_class(AlphaVantage)
        template.asset_type_overrides = {
            'ETH': AssetType.DIGITAL_CURRENCY,
            'LTC': AssetType.DIGITAL_CURRENCY
        }

        script_dir = os.path.dirname(os.path.realpath(__file__))
        strategy_date_dir = FileSystem.get_and_clean_cache_dir(
            os.path.join(script_dir, '..', '..', '..', '.cache', 'strategies'))

        # Strategies
        strategies: List[Strategy] = []

        strategies.append(BuyAndHold(symbol, copy.deepcopy(template)))

        # strategies.append(BookDepth(symbol, copy.deepcopy(template), period=14.0))

        thresholds = [
            # 0.001, 0.005,
            0.01,
            # 0.02, 0.03,
        ]
        ratios = [
            # 0.25, 0.5, 0.75,
            # 1.0, 1.5,
            2.0,
            # 2.5, 3.0,
        ]
        for threshold in thresholds:
            for ratio in ratios:
                strategies.append(LastBounce(symbol, copy.deepcopy(template), ratio, threshold))
                pass

        buy_downs = [
            # 0.9
            0.975,
            # 1.025,
        ]
        sell_ups = [
            # 0.975, 1.025,
            1.1,
            # 1.2,
        ]
        for buy_down in buy_downs:
            for sell_up in sell_ups:
                strategies.append(BuyDownSellUpTrailing(symbol, copy.deepcopy(template), buy_down, sell_up))
                pass

        buy_ups = [
            # 1.025, 1.05, 1.1, 1.2, 1.3, 1.4, 1.5,
            1.6,
            # 1.7,
        ]
        sell_downs = [
            # 0.975, 0.95, 0.9, 0.8, 0.7,
            0.6,
            # 0.5, 0.4, 0.3,
        ]
        for buy_up in buy_ups:
            for sell_down in sell_downs:
                strategies.append(BuyUpSellDownTrailing(symbol, copy.deepcopy(template), buy_up, sell_down))
                pass
        # strategies[0].collection.symbol_adapters[symbol].data_adapters[QueryType.SERIES].span = 'year'  # '3month' 'week'

        strategies.append(SoldiersAndCrows(symbol, copy.deepcopy(template), count=3))

        # (RSI)
        rsi_uppers = [  # Fast (Exponential) Moving Average in number of intervals (days if daily, months if monthly etc.)
            # 50.0,
            60.0,
            # 75.0,
        ]
        rsi_lowers = [  # Slow (Exponential) Moving Average
            # 25.0,
            40.0,
            # 65.0,
        ]
        rsi_periods = [  # MACD = Fast EMA - Slow EMA, a trigger to buy is when MACD goes above Signal e.g. 9 day EMA
            # 12.0,
            14.0,
            # 16.0,
        ]
        for rsi_upper in rsi_uppers:
            for rsi_lower in rsi_lowers:
                for rsi_period in rsi_periods:
                    strategies.append(BoundedRsi(symbol, copy.deepcopy(template), rsi_period, rsi_upper, rsi_lower))
                    pass

        # Moving Average Convergence Divergence (MACD)
        macd_fasts = [  # Fast (Exponential) Moving Average in number of intervals (days if daily, months if monthly etc.)
            # 6.0,
            12.0,
            # 18.0, 24.0,
        ]
        macd_slows = [  # Slow (Exponential) Moving Average
            # 24.0,
            26.0,
            # 52.0, 104.0, 208.0,
        ]
        macd_signals = [  # MACD = Fast EMA - Slow EMA, a trigger to buy is when MACD goes above Signal e.g. 9 day EMA
            # 7.0, 8.0,
            9.0,
            # 10.0, 11.0,
        ]
        for macd_fast in macd_fasts:
            for macd_slow in macd_slows:
                for macd_signal in macd_signals:
                    strategies.append(MacdCrossing(symbol, copy.deepcopy(template), macd_slow, macd_fast, macd_signal))
                    pass

        # success = True
        # for strategy in strategies:
        #     strategy.run()
        # report_on = strategies

        # strategy_runner = SequentialStrategyExecutor(strategy_date_dir)
        strategy_runner = ParallelStrategyExecutor(strategy_date_dir)
        for strategy in strategies:
            # whitelist = [MacdCrossing]
            whitelist = []
            if len(whitelist) > 0 and strategy.__class__ not in whitelist:
                continue
            key = str(strategy).replace(' ', '_')
            strategy_runner.add_strategy(strategy.run, (), symbol, key)
        success = strategy_runner.start()
        report_on = strategy_runner.processed_strategies[symbol]

        title = 'Symbol Runner - Strategy Comparison {}'.format(
            symbol)  # - {} - {} to {}'.format(symbol, start_time, end_time)
        self.summarize(title, report_on)

        # call directly
        # for strategy in report_on:
        #     visualizer: Visualizer = Visualizer(str(strategy), strategy.collection, [strategy.portfolio])
        #     visualizer.plot_all()

        # draw = True
        draw = False
        if draw:
            visual_date_dir = FileSystem.get_and_clean_cache_dir(
                os.path.join(script_dir, '..', '..', '..', '.cache', 'visuals'))
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
