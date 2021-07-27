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
from typing import List, Dict

from main.application.adapter import TimeInterval, AssetType
from main.adapters.alpha_vantage import AlphaVantage
from main.application.value_type import ValueType
from main.common.locations import get_and_clean_timestamp_dir
from main.executors.parallel_executor import ParallelExecutor
from main.executors.parallel_strategy_executor import ParallelStrategyExecutor
from main.portfolio.portfolio import Portfolio
from main.application.runner import Runner
from main.strategies.buy_and_hold import BuyAndHold
from main.strategies.buy_down_sell_up_trailing import BuyDownSellUpTrailing
from main.strategies.buy_up_sell_down_trailing import BuyUpSellDownTrailing
from main.strategies.last_bounce import LastBounce
from main.strategies.soldiers_and_crows import SoldiersAndCrows
from main.application.strategy import Strategy
from main.visual.visualizer import Visualizer


class MatrixRunner(Runner):
    symbols: List[str]

    def __init__(self):
        super().__init__()
        self.symbols = []

    def summarize(self, title: str, strategy_matrix: Dict[str, List[Strategy]]):
        logging.info('== {}'.format(title))
        column = 0
        results = {}
        dates = {}
        totals = {}
        first = True
        for symbol in self.symbols:
            results[symbol] = {}
            for strategy in strategy_matrix[symbol]:
                portfolio = strategy.portfolio
                if first:
                    spaces = " " * 14 * column
                    logging.info('{:>15} : {}{}'.format("", spaces, portfolio.title))
                    column += 1
                interest_rate = portfolio.calculate_cagr()
                results[symbol][portfolio.title] = interest_rate
                dates[symbol] = [strategy.collection.get_start_time(symbol, ValueType.CLOSE),
                                 strategy.collection.get_end_time(symbol, ValueType.CLOSE)]
                if portfolio.title not in totals:
                    totals[portfolio.title] = 0.0
                totals[portfolio.title] += interest_rate
            first = False
        win_counts = {}
        for symbol, rates in results.items():
            line = ""
            winner = None
            win_rate = 0.0
            for title, rate in rates.items():
                line += '{:12.2f} %'.format(rate * 100.0)
                if title not in win_counts:
                    win_counts[title] = 0
                if winner is None or rate > win_rate:
                    winner = title
                    win_rate = rate
            win_counts[winner] += 1
            line += " (data {} to {}) ".format(dates[symbol][0], dates[symbol][1])
            logging.info('{:>15} : {}'.format(symbol, line))
        line = ""
        count = float(len(self.symbols))
        for title, total in totals.items():
            line += '{:12.2f} %'.format(total / count * 100.0)
        logging.info('{:>15} : {}'.format("Average", line))
        line = ""
        for title, wins in win_counts.items():
            line += '{:12d}  '.format(wins)
        logging.info('{:>15} : {}'.format("Wins", line))

    def start(self):
        logging.info("#### Starting matrix runner...")

        self.symbols = [
            # Technology
            'AAPL',  # Consumer Electronics
            'MSFT',  # Software / Infrastructure
            'NVDA', 'INTC', 'AVGO',
            'AMD', 'XLNX', 'TSM',  # Semiconductors
            'GHVI',  # MatterPort
            # Communication Services
            'GOOG', 'FB',  # Internet Information
            'VZ', 'T',  # Telecommunications
            'NFLX', 'DIS',  # Entertainment
            # Commercial
            'AMZN',  # Internet Retail
            'TSLA',  # Automotive Manufacturing
            'HD',  # Home Improvement
            # Financial
            'V', 'MA', 'AXP',  # Credit Services
            'JPM', 'BAC', 'C', 'WFC',  # Banks - Diversified
            'BRK-B', 'AIG',  # Insurance - Diversified
            # Foods
            'TTCF',  # Buy at 18
            'BYND',  # 'IMPM',  # Buy impossible at $120
            # Bonds
            'TLT',
            # Real Estate
            'EXPI',
            # Farm / Commodities
            'DE', 'UHAL',
            # 'CAKE',
            # Using Bitcoint - TSLA is too
            # 'MSTR',  # Microstrategy - $500M cash sitting, $250M buy own stock, $250M into bitcoin to preserve it
            # Dividend + Reinvest
            # 'FSKR',
            # MJ
            # 'GGTTF',
            # Payments
            'SQ', 'PYPL', 'SNOW', 'NVTA', 'FROG',
            # SPACs
            # 'IPOE', 'CCIX',
            'CCIV',
            # ETFs
            'ARKW', 'ARKQ', 'ARKF', 'ARKK', 'ARKG', 'PRNT', 'IZRL', 'SOXX',
            # Alternative Medicine
            'CMPS', 'MNMD',
            # Digital Currencies
            'BTC', 'ETH', 'LTC', 'DOGE',
            # Whole Market
            'VTI',
            # Sectors
            'XLF',  # Financial
            'XLK',  # Technology
            'XLI',  # Industrial
            'XLB',  # Materials
            'XLV',  # Health Care
            'XLU',  # Utilities
            'XLE',  # Energy
            'XLP',  # Consumer Staples
            'XLY',  # Consumer Discretionary
            # World
            'EWT',  # Taiwan
            'VT',  # Whole world
        ]

        script_dir = os.path.dirname(os.path.realpath(__file__))
        strategy_date_dir = get_and_clean_timestamp_dir()

        # strategy_runner = SequentialStrategyExecutor(strategy_date_dir)
        strategy_runner = ParallelStrategyExecutor(strategy_date_dir)

        strategy_matrix: Dict[str, List[Strategy]] = {}
        for symbol in self.symbols:
            strategy_matrix[symbol] = []
            self.add_symbol_strategies(symbol, strategy_matrix)

        for symbol, strategies in strategy_matrix.items():
            for strategy in strategies:
                strategy_runner.add_strategy(strategy.run, (), symbol, str(strategy).replace(' ', '_'))
                # break
            # break
        success = strategy_runner.start()

        title = 'Strategies Across Symbols CAGR'
        self.summarize(title, strategy_runner.processed_strategies)

        # draw = True
        draw = False
        if draw:
            visual_date_dir = get_and_clean_timestamp_dir()
            visual_runner = ParallelExecutor(visual_date_dir)
            for symbol in self.symbols:
                for strategy in strategy_runner.processed_strategies[symbol]:
                    visualizer: Visualizer = Visualizer(str(strategy), strategy.collection, [strategy.portfolio])
                    # visualizer.annotate_canceled_orders = True
                    visualizer.annotate_opened_orders = True
                    # visualizer.annotate_open_prices = True
                    # visualizer.annotate_close_prices = True
                    # visualizer.draw_high_prices = False
                    # visualizer.draw_low_prices = False
                    # visualizer.draw_open_prices = True
                    # visualizer.draw_close_prices = True
                    visual_runner.add(visualizer.plot_all, (), str(strategy).replace(' ', '_'))
            visual_runner.start()
        return success

    @staticmethod
    def add_symbol_strategies(symbol, strategies):
        # Portfolio
        template: Portfolio = Portfolio('Multi-Symbol Portfolio Value', {'USD': 10000.0, symbol: 0.0})
        template.base_symbol = 'USD'
        template.start_time = datetime(2020, 10, 19)
        template.add_adapter_class(AlphaVantage)
        template.asset_type_overrides = {
            'ETH': AssetType.DIGITAL_CURRENCY,
            'LTC': AssetType.DIGITAL_CURRENCY
        }
        # Interval
        intervals = [
            # TimeInterval.WEEK,
            TimeInterval.DAY,
        ]

        # Strategies

        strategies[symbol].append(BuyAndHold(symbol, copy.deepcopy(template)))

        thresholds = [
            0.05,
            # 0.04, 0.03, 0.02,
            # 0.01,
            # 0.005,
        ]
        ratios = [
            # 0.9, 0.8, 0.7, 0.6,
            0.5,
            # 0.4, 0.3,
        ]
        for threshold in thresholds:
            for ratio in ratios:
                for interval in intervals:
                    template.interval = interval
                    strategies[symbol].append(LastBounce(symbol, copy.deepcopy(template), ratio, threshold))
                    pass

        sell_ups = [
            # 1.025, 1.05, 1.1, 1.2, 1.3, 1.4, 1.5,
            1.3,
            # 1.4, 1.5, 1.6, 1.7,
        ]
        buy_downs = [
            # 0.975, 0.95, 0.9, 0.8, 0.7, 0.54,
            0.6,
            # 0.66, 0.5, 0.4, 0.3,
        ]
        for sell_up in sell_ups:
            for buy_down in buy_downs:
                for interval in intervals:
                    template.interval = interval
                    strategies[symbol].append(BuyDownSellUpTrailing(symbol, copy.deepcopy(template), buy_down, sell_up))
                    pass

        buy_ups = [
            # 1.025, 1.05, 1.1, 1.2, 1.3, 1.4, 1.5, 1.3, 1.4,
            1.5,
            # 1.6,
            # 1.7,
        ]
        sell_downs = [
            # 0.975, 0.95, 0.9, 0.8, 0.7,
            # 0.54,
            0.6,
            # 0.66,
            # 0.5, 0.4, 0.3,
        ]
        busd_intervals = [
            TimeInterval.WEEK,
            # TimeInterval.DAY,
        ]
        for buy_up in buy_ups:
            for sell_down in sell_downs:
                for interval in busd_intervals:
                    template.interval = interval
                    strategies[symbol].append(BuyUpSellDownTrailing(symbol, copy.deepcopy(template), buy_up, sell_down))
                    pass

        counts = [
            # 2,
            3,
            # 4, 5,
        ]
        for count in counts:
            for interval in intervals:
                template.interval = interval
                strategies[symbol].append(SoldiersAndCrows(symbol, copy.deepcopy(template), count))
                pass

        # Some digital currencies do not support WEEKLY with RSI, MACD, etc. (for certain data adapters)
        # if template.interval == TimeInterval.DAY:
        #     strategies[symbol].append(BoundedRsi(symbol, copy.deepcopy(template), period=14.0, upper=60.0, lower=40.0))
        #     strategies[symbol].append(BoundedRsi(symbol, copy.deepcopy(template), period=14.0, upper=75.0, lower=25.0))
        #     strategies[symbol].append(BoundedRsi(symbol, copy.deepcopy(template), period=14.0, upper=50.0, lower=40.0))
        #     strategies[symbol].append(MacdCrossing(symbol, copy.deepcopy(template), slow=26.0, fast=12.0, signal=9.0))