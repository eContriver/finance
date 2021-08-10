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
from enum import Enum, auto
from typing import List, Dict, Optional

from main.application.adapter import TimeInterval, AssetType
from main.adapters.iex_cloud import IexCloud
from main.common.locations import get_and_clean_timestamp_dir, Locations
from main.executors.parallel_executor import ParallelExecutor
from main.executors.sequential_strategy_executor import SequentialStrategyExecutor
from main.portfolio.portfolio import Portfolio
from main.application.runner import Runner, get_asset_type_overrides, get_adapter_class, NoSymbolsSpecifiedException
from main.strategies.bounded_rsi import BoundedRsi
from main.strategies.buy_and_hold import BuyAndHold
from main.strategies.buy_down_sell_up_trailing import BuyDownSellUpTrailing
from main.strategies.buy_up_sell_down_trailing import BuyUpSellDownTrailing
from main.strategies.last_bounce import LastBounce
from main.strategies.macd_crossing import MacdCrossing
from main.strategies.soldiers_and_crows import SoldiersAndCrows
from main.application.strategy import Strategy
from main.visual.visualizer import Visualizer


class StrategyResultsAreEmptyException(RuntimeError):
    pass


class SymbolReportType(Enum):
    BUY_AND_HOLD = auto()
    LAST_BOUNCE = auto()
    BUY_DOWN_SELL_UP_TRAILING = auto()
    BUY_UP_SELL_DOWN_TRAILING = auto()
    SOLDIERS_AND_CROWS = auto()
    BOUNDED_RSI = auto()
    MACD_CROSSING = auto()


class SymbolRunner(Runner):
    symbol: Optional[str]
    adapter_class: Optional[type]
    base_symbol: str
    price_interval: TimeInterval
    asset_type_overrides: Dict[str, AssetType]
    report_types: List[SymbolReportType]
    graph: bool

    def __init__(self):
        super().__init__()
        self.symbol = None
        self.adapter_class = None
        self.base_symbol = 'USD'
        self.price_interval = TimeInterval.DAY
        self.asset_type_overrides = {}
        self.report_types = []
        self.graph = False

    def get_config(self) -> Dict:
        asset_type_overrides = {}
        for symbol, asset_type in self.asset_type_overrides.items():
            asset_type_overrides[self.symbol] = asset_type.name
        config = {
            'adapter_class': self.adapter_class.__name__,
            'base_symbol': self.base_symbol,
            'symbol': self.symbol,
            'graph': self.graph,
            'price_interval': self.price_interval.value,
            'asset_type_overrides': asset_type_overrides,
            'report_types': [report_type.name for report_type in self.report_types],
        }
        return config

    def set_from_config(self, config, config_path):
        self.symbol = config['symbol']
        self.adapter_class = get_adapter_class(config['adapter_class'])
        report_types: List[str] = config['report_types']
        self.report_types = [SymbolReportType[report_type] for report_type in report_types]
        if 'asset_type_overrides' in config:
            self.asset_type_overrides = get_asset_type_overrides(config['asset_type_overrides'])
        if 'graph' in config:
            self.graph = config['graph']
        if 'base_symbol' in config:
            self.base_symbol = config['base_symbol']
        if 'price_interval' in config:
            self.price_interval = TimeInterval(config['price_interval'])
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

        start_time = None
        # start_time = datetime.now() - (2 * TimeInterval.YEAR.timedelta)
        end_time = None
        # end_time = datetime(2010, 1, 1)
        template: Portfolio = Portfolio('Single Symbol Portfolio Value', {'USD': 20000.0, self.symbol: 0.0},
                                        start_time, end_time)
        # template.interval = TimeInterval.DAY
        template.interval = TimeInterval.WEEK
        template.add_adapter_class(self.adapter_class)
        template.asset_type_overrides = self.asset_type_overrides

        # script_dir = os.path.dirname(os.path.realpath(__file__))
        strategy_date_dir = get_and_clean_timestamp_dir(locations.get_cache_dir('strategies'))

        # Strategies
        strategies: List[Strategy] = []

        if SymbolReportType.BUY_AND_HOLD in self.report_types:
            strategies.append(BuyAndHold(self.symbol, copy.deepcopy(template)))

        # strategies.append(BookDepth(self.symbol, copy.deepcopy(template), period=14.0))

        if SymbolReportType.LAST_BOUNCE in self.report_types:
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
                    strategies.append(LastBounce(self.symbol, copy.deepcopy(template), ratio, threshold))
                    pass

        if SymbolReportType.BUY_DOWN_SELL_UP_TRAILING in self.report_types:
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
                    strategies.append(BuyDownSellUpTrailing(self.symbol, copy.deepcopy(template), buy_down, sell_up))
                    pass

        if SymbolReportType.BUY_UP_SELL_DOWN_TRAILING in self.report_types:
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
                    strategies.append(BuyUpSellDownTrailing(self.symbol, copy.deepcopy(template), buy_up, sell_down))
                    pass

        if SymbolReportType.SOLDIERS_AND_CROWS in self.report_types:
            count = 3
            strategies.append(SoldiersAndCrows(self.symbol, copy.deepcopy(template), count))

        if SymbolReportType.BOUNDED_RSI in self.report_types:
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
                        strategies.append(BoundedRsi(self.symbol, copy.deepcopy(template), rsi_period, rsi_upper, rsi_lower))
                        pass

        if SymbolReportType.MACD_CROSSING in self.report_types:
            # Fast (Exponential) Moving Average in number of intervals (days if daily, months if monthly etc.)
            macd_fasts = [
                # 6.0,
                12.0,
                # 18.0, 24.0,
            ]
            # Slow (Exponential) Moving Average
            macd_slows = [
                # 24.0,
                26.0,
                # 52.0, 104.0, 208.0,
            ]
            # MACD = Fast EMA - Slow EMA, a trigger to buy is when MACD goes above Signal e.g. 9 day EMA
            macd_signals = [
                # 7.0, 8.0,
                9.0,
                # 10.0, 11.0,
            ]
            for macd_fast in macd_fasts:
                for macd_slow in macd_slows:
                    for macd_signal in macd_signals:
                        strategies.append(MacdCrossing(self.symbol, copy.deepcopy(template), macd_slow, macd_fast, macd_signal))
                        pass

        # success = True
        # for strategy in strategies:
        #     strategy.run()
        # report_on = strategies

        strategy_runner = SequentialStrategyExecutor(strategy_date_dir)
        # strategy_runner = ParallelStrategyExecutor(strategy_date_dir)
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

        title = 'Symbol Runner - Strategy Comparison {}'.format(
            self.symbol)  # - {} - {} to {}'.format(self.symbol, start_time, end_time)
        summarize(title, report_on)

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
