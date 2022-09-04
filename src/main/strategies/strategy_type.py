#  Copyright 2021-2022 eContriver LLC
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
from enum import Enum, auto
from typing import List

from main.application.strategy import Strategy
from main.strategies.bounded_rsi import BoundedRsi
from main.strategies.buy_and_hold import BuyAndHold
from main.strategies.testing.sma_up import SMAUp
from main.strategies.testing.testing_atr import TestingATR
from main.strategies.testing.testing_macd import TestingMACD
from main.strategies.testing.testing_supertrend import TestingSUPERTREND
from main.strategies.testing.testing_wma import TestingWMA
from main.strategies.testing.testing_ema import TestingEMA
from main.strategies.testing.testing_lindev import TestingLINDEV
from main.strategies.buy_down_sell_up_trailing import BuyDownSellUpTrailing
from main.strategies.buy_up_sell_down_trailing import BuyUpSellDownTrailing
from main.strategies.last_bounce import LastBounce
from main.strategies.macd_crossing import MacdCrossing
from main.strategies.multi_delta_swap import MultiDeltaSwap
from main.strategies.multi_relative_sma_swap_down import MultiRelativeSmaSwapDown
from main.strategies.multi_relative_sma_swap_up import MultiRelativeSmaSwapUp
from main.strategies.soldiers_and_crows import SoldiersAndCrows


class StrategyType(Enum):
    BUY_AND_HOLD = auto()
    SMA_UP = auto()
    TESTING_ATR = auto()
    TESTING_MACD = auto()
    TESTING_SUPERTREND = auto()
    TESTING_WMA= auto()
    TESTING_EMA = auto()
    TESTING_LINDEV = auto()
    LAST_BOUNCE = auto()
    BUY_DOWN_SELL_UP_TRAILING = auto()
    BUY_UP_SELL_DOWN_TRAILING = auto()
    SOLDIERS_AND_CROWS = auto()
    BOUNDED_RSI = auto()
    MACD_CROSSING = auto()
    MULTI_DELTA_SWAP = auto()
    MULTI_RELATIVE_SMA_SWAP_UP = auto()
    MULTI_RELATIVE_SMA_SWAP_DOWN = auto()


def add_buy_and_hold_strategies(report_types, symbols, template):
    strategies: List[Strategy] = []
    if StrategyType.BUY_AND_HOLD in report_types:
        for symbol in symbols:
            strategies.append(BuyAndHold(symbol, copy.deepcopy(template)))
    return strategies


def add_sma_up_strategies(report_types, symbols, template):
    strategies: List[Strategy] = []
    if StrategyType.SMA_UP in report_types:

        #  ALL OF THIS
        for symbol in symbols:
            strategies.append(SMAUp(symbol, copy.deepcopy(template)))
    return strategies


def add_testing_atr_strategies(report_types, symbols, template):
    strategies: List[Strategy] = []
    if StrategyType.TESTING_ATR in report_types:

        #  ALL OF THIS
        for symbol in symbols:
            strategies.append(TestingATR(symbol, copy.deepcopy(template)))
    return strategies

def add_testing_macd_strategies(report_types, symbols, template):
    strategies: List[Strategy] = []
    if StrategyType.TESTING_MACD in report_types:

        #  ALL OF THIS
        for symbol in symbols:
            strategies.append(TestingMACD(symbol, copy.deepcopy(template)))
    return strategies

def add_testing_supertrend_strategies(report_types, symbols, template):
    strategies: List[Strategy] = []
    if StrategyType.TESTING_SUPERTREND in report_types:

        #  ALL OF THIS
        for symbol in symbols:
            strategies.append(TestingSUPERTREND(symbol, copy.deepcopy(template)))
    return strategies

def add_testing_wma_strategies(report_types, symbols, template):
    strategies: List[Strategy] = []
    if StrategyType.TESTING_WMA in report_types:

        #  ALL OF THIS
        for symbol in symbols:
            strategies.append(TestingWMA(symbol, copy.deepcopy(template)))
    return strategies

def add_testing_ema_strategies(report_types, symbols, template):
    strategies: List[Strategy] = []
    if StrategyType.TESTING_EMA in report_types:

        #  ALL OF THIS
        for symbol in symbols:
            strategies.append(TestingEMA(symbol, copy.deepcopy(template)))
    return strategies


def add_testing_lindev_strategies(report_types, symbols, template):
    strategies: List[Strategy] = []
    if StrategyType.TESTING_LINDEV in report_types:

        #  ALL OF THIS
        for symbol in symbols:
            strategies.append(TestingLINDEV(symbol, copy.deepcopy(template)))
    return strategies

def add_last_bounce_strategies(report_types, symbols, template):
    strategies: List[Strategy] = []
    if StrategyType.LAST_BOUNCE in report_types:
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
                for symbol in symbols:
                    strategies.append(LastBounce(symbol, copy.deepcopy(template), ratio, threshold))
    return strategies


def add_macd_crossing_strategies(report_types, symbols, template):
    strategies: List[Strategy] = []
    if StrategyType.MACD_CROSSING in report_types:
        # Fast (Exponential) Moving Average in number of intervals (days if daily, months if monthly etc.)
        macd_fasts = [
            # 6.0,
            12.0, 13.0,
            # 18.0, 24.0,
        ]
        # Slow (Exponential) Moving Average
        macd_slows = [
            # 24.0,
            26.0, 34.0,
            # 52.0, 104.0, 208.0,
        ]
        # MACD = Fast EMA - Slow EMA, a trigger to buy is when MACD goes above Signal e.g. 9 day EMA
        macd_signals = [
            7.0, 8.0,
            9.0,
            # 10.0, 11.0,
        ]
        for macd_fast in macd_fasts:
            for macd_slow in macd_slows:
                for macd_signal in macd_signals:
                    for symbol in symbols:
                        strategies.append(
                            MacdCrossing(symbol, copy.deepcopy(template), macd_slow, macd_fast, macd_signal))
    return strategies


def add_bounded_rsi_strategies(report_types, symbols, template):
    strategies: List[Strategy] = []
    if StrategyType.BOUNDED_RSI in report_types:
        rsi_uppers = [
            # Fast (Exponential) Moving Average in number of intervals (days if daily, months if monthly etc.)
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
                    for symbol in symbols:
                        strategies.append(
                            BoundedRsi(symbol, copy.deepcopy(template), rsi_period, rsi_upper, rsi_lower))
    return strategies


def add_buy_up_sell_down_trailing_strategies(report_types, symbols, template):
    strategies: List[Strategy] = []
    if StrategyType.BUY_UP_SELL_DOWN_TRAILING in report_types:
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
                for symbol in symbols:
                    strategies.append(BuyUpSellDownTrailing(symbol, copy.deepcopy(template), buy_up, sell_down))
    return strategies


def add_buy_down_sell_up_trailing_strategies(report_types, symbols, template):
    strategies: List[Strategy] = []
    if StrategyType.BUY_DOWN_SELL_UP_TRAILING in report_types:
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
                for symbol in symbols:
                    strategies.append(BuyDownSellUpTrailing(symbol, copy.deepcopy(template), buy_down, sell_up))
    return strategies


def add_soldiers_and_crows_strategies(report_types, symbols, template):
    strategies: List[Strategy] = []
    if StrategyType.SOLDIERS_AND_CROWS in report_types:
        count = 3
        for symbol in symbols:
            strategies.append(SoldiersAndCrows(symbol, copy.deepcopy(template), count))
    return strategies


def add_multi_delta_swap_strategies(report_types, symbols, template):
    strategies: List[Strategy] = []
    if StrategyType.MULTI_DELTA_SWAP in report_types:
        deltas = [
            1.1,
            # 1.05,
            # 1.025,
        ]
        for delta in deltas:
            strategies.append(MultiDeltaSwap(symbols, copy.deepcopy(template), delta=delta))
    return strategies


def add_multi_relative_sma_swap_up_strategies(report_types, symbols, template):
    strategies: List[Strategy] = []
    if StrategyType.MULTI_RELATIVE_SMA_SWAP_UP in report_types:
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
        periods = [20.0]
        for period in periods:
            for delta in deltas:
                for look_back in look_backs:
                    strategies.append(
                        MultiRelativeSmaSwapUp(symbols, copy.deepcopy(template), period, delta, look_back))
    return strategies


def add_multi_relative_sma_swap_dowm_strategies(report_types, symbols, template):
    strategies: List[Strategy] = []
    if StrategyType.MULTI_RELATIVE_SMA_SWAP_DOWN in report_types:
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
        periods = [20.0]
        for period in periods:
            for delta in deltas:
                for look_back in look_backs:
                    strategies.append(
                        MultiRelativeSmaSwapDown(symbols, copy.deepcopy(template), period, delta, look_back))
    return strategies
