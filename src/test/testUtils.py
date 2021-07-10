#!/usr/local/bin/python

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

import inspect
import logging
import math
from datetime import datetime, timedelta
from typing import Optional, List, Dict

import pandas

from main.adapters.adapter import TimeInterval, AssetType, Adapter
from main.adapters.converter import Converter
from main.adapters.valueType import ValueType
from main.adapters.adapterCollection import AdapterCollection

from main.adapters.argument import ArgumentType, Argument


class DataGenerator:
    def __init__(self, periods: int, end_time: datetime, start_price: float,
                 interval: TimeInterval = TimeInterval.DAY):
        self.periods: int = periods
        self.end_time: datetime = end_time
        self.start_price: float = start_price
        self.interval: TimeInterval = interval
        self.static_values: Dict[ValueType, float] = {ValueType.VOLUME: 100000}
        self.base_offsets: Dict[ValueType, float] = {ValueType.HIGH: 1.0,
                                                     ValueType.CLOSE: 0.5,
                                                     ValueType.OPEN: -0.5,
                                                     ValueType.LOW: -1.0,
                                                     ValueType.RSI: 0.0
                                                     }

    def get_base_price(self, period: int) -> float:
        raise RuntimeError("Implement: {}".format(inspect.currentframe().f_code.co_name))

    def get_data(self, get_value_type: ValueType) -> pandas.DataFrame:
        translated: pandas.DataFrame = pandas.DataFrame()
        # self.end_time = datetime.now() if self.end_time is None else self.end_time
        start_time = self.end_time - (self.interval.timedelta * self.periods)
        for i in range(self.periods):
            current_time: datetime = start_time + (self.interval.timedelta * i)
            # translated[current_time] = {}
            price: float = self.get_base_price(i)
            for value_type, offset in self.base_offsets.items():
                # if value_type == get_value_type:
                #     continue
                adjusted_offset = offset
                if i > 0 and (value_type == ValueType.OPEN or value_type == ValueType.CLOSE):
                    adjusted_offset *= 1.0 if price > self.get_base_price(i - 1) else -1.0
                translated.loc[current_time, value_type] = price + adjusted_offset
            for value_type, offset in self.static_values.items():
                # if value_type == get_value_type:
                #     continue
                translated.loc[current_time, value_type] = offset
        return translated


class LinearGenerator(DataGenerator):
    def __init__(self, periods: int, end_time: datetime, start_price: float,
                 interval: TimeInterval = TimeInterval.DAY):
        super(LinearGenerator, self).__init__(periods, end_time, start_price, interval)
        self.slope: float = 1.0
        self.n: float = 1.0

    def get_base_price(self, period: int):
        price: float = self.slope * float(period) ** self.n + self.start_price  # y = m * x ^ n + b
        return price


class SineGenerator(DataGenerator):
    def __init__(self, periods: int, end_time: datetime, start_price: float,
                 interval: TimeInterval = TimeInterval.DAY):
        super(SineGenerator, self).__init__(periods, end_time, start_price, interval)
        self.frequency: float = math.pi / 2
        self.amplitude: float = 5.0

    def get_base_price(self, period: int):
        price: float = math.sin(
            self.frequency * float(period)) * self.amplitude + self.start_price  # y = sin(f * x) * a * + b
        return price


class StepGenerator(DataGenerator):
    def __init__(self, periods: int, end_time: datetime, start_price: float,
                 interval: TimeInterval = TimeInterval.DAY):
        super(StepGenerator, self).__init__(periods, end_time, start_price, interval)

    def get_base_price(self, period: int):
        slope = 1.01
        price = slope * period + self.start_price
        cycle = 18
        if (period - 4) % cycle == 0:
            price *= 0.95
        elif (period - 5) % cycle == 0:
            price *= 1.05
        elif (period - 6) % cycle == 0 or (period - 7) % cycle == 0 or (period - 8) % cycle == 0:
            price *= 1.10
        elif (period - 9) % cycle == 0:
            price *= 1.05
        elif (period - 12) % cycle == 0:
            price *= 1.05
        elif (period - 13) % cycle == 0:
            price *= 0.95
        elif (period - 14) % cycle == 0 or (period - 15) % cycle == 0 or (period - 16) % cycle == 0:
            price *= 0.90
        elif (period - 17) % cycle == 0:
            price *= 0.95
        return price


class MockDataAdapter(Adapter):
    def __init__(self, symbol: str, asset_type: Optional[AssetType] = None):
        super().__init__(symbol, asset_type)
        self.converters: List[Converter] = [
            # we allow for multiple strings to be converted into the value type, first match is used
            Converter(ValueType.OPEN, self.get_data, ['1. open', '1a. open (USD)'], adjust_values=True),
            Converter(ValueType.HIGH, self.get_data, ['2. high', '2a. high (USD)'], adjust_values=True),
            Converter(ValueType.LOW, self.get_data, ['3. low', '3a. low (USD)'], adjust_values=True),
            Converter(ValueType.CLOSE, self.get_data, ['4. close', '4a. close (USD)'], adjust_values=True),
            Converter(ValueType.VOLUME, self.get_data, ['5. volume']),
            Converter(ValueType.RSI, self.get_data, ['RSI']),
            Converter(ValueType.MACD, self.get_data, ['MACD']),
            Converter(ValueType.MACD_HIST, self.get_data, ['MACD_Hist']),
            Converter(ValueType.MACD_SIGNAL, self.get_data, ['MACD_Signal']),
            # SMA = auto()
            # BOOK = auto()
            Converter(ValueType.EPS, self.get_data, ['reportedEPS']),
            # ESTIMATED_EPS = auto()
            # SURPRISE_EPS = auto()
            # SURPRISE_PERCENTAGE_EPS = auto()
            # GROSS_PROFIT = auto()
            # TOTAL_REVENUE = auto()
            # OPERATING_CASH_FLOW = auto()
            Converter(ValueType.DIVIDENDS, self.get_data, ['dividendPayout']),
            Converter(ValueType.NET_INCOME, self.get_data, ['netIncome']),
            Converter(ValueType.ASSETS, self.get_data, ['totalAssets']),
            Converter(ValueType.LIABILITIES, self.get_data, ['totalLiabilities']),
            # This value was very wrong for BRK-A, it says something like 3687360528 shares outstanding, while there
            # are actually only something like 640000
            Converter(ValueType.OUTSTANDING_SHARES, self.get_data, ['commonStockSharesOutstanding']),
            # This is not quite right...
            # https://www.fool.com/investing/stock-market/basics/earnings-per-share/

            # Let's walk through an example EPS calculation using Netflix (NASDAQ:NFLX). For its most recent fiscal
            # year, the company reported a net income of $2,761,395,000 and total shares outstanding of 440,922,
            # 000. The company's balance sheet indicates Netflix has not issued any preferred stock, so we don't need
            # to subtract out preferred dividends. Dividing $2,761,395,000 into 440,922,000 produces an EPS value of
            # $6.26. (this is what we get, and even then the number of outstanding shares differs slightly)
            #
            # Let's calculate the diluted EPS for Netflix. The company has granted 13,286,000 stock options to
            # employees, which raises the total outstanding share count to 454,208,000. Dividing the same $2,761,395,
            # 000 of net income into 454,208,000 equals an EPS value of $6.08.
            Converter(ValueType.DILUTED_SHARES, self.get_data, ['commonStockSharesOutstanding']),
            Converter(ValueType.SHAREHOLDER_EQUITY, self.get_data, ['totalShareholderEquity']),
        ]

    # def collect_data(self, value_type: ValueType):
    #     super(SeriesAdapter, self).collect_data(value_type)
    #     super(RsiAdapter, self).collect_data(value_type)

    def get_data(self, value_type: ValueType):
        generator: DataGenerator = self.get_generator()
        self.data = generator.get_data(value_type)

    def get_generator(self) -> DataGenerator:
        # up/down
        periods = 20
        interval: TimeInterval = self.get_argument_value(ArgumentType.INTERVAL)
        end_time: datetime = self.get_argument_value(ArgumentType.END_TIME)
        end_time = datetime.now() if end_time is None else end_time
        # end_time = self.cache_key_date
        assert interval is not None, "The interval argument was not specified, found: {}".format(interval)
        # sine - we want more samples with sine, so multiple by 4
        samples_per_period = 4
        cycles_per_plot = 2  # means 2 cycles in this 1 set of self.data (x periods)
        sine_interval = TimeInterval.HOUR6  # TimeInterval.get(interval.timedelta / samples_per_period)
        assert sine_interval == TimeInterval.HOUR6, "The interval ({}) was set to 6HOURS it must align with samples per period: 24hours/{}".format(
            sine_interval, samples_per_period)
        # frequency (rad/sample) = 2 pi (rad/cycle) * 2 (cycles/plot) / ( 1 plot * 4 (sample/period) * 10 periods)
        frequency = (2.0 * math.pi) * cycles_per_plot / (samples_per_period * periods)
        generator = None
        # up
        if self.symbol == 'UP15':  # close is 15 to 25 = x + 15
            generator = LinearGenerator(periods, end_time, 14.5, interval)
        elif self.symbol == 'UP20':  # close is 20 to 40 = 2 * x + 20
            generator = LinearGenerator(periods, end_time, 19.5, interval)
            generator.slope = 2.0
        elif self.symbol == 'UP25':  # close is 25 to 125 = x ^ 2 + 25
            generator = LinearGenerator(periods, end_time, 24.5, interval)
            generator.slope = 1.0
            generator.n = 2.0
        elif self.symbol == 'UP30':  # close is 30 to 1030 = x ^ 3 + 30
            generator = LinearGenerator(periods, end_time, 29.5, interval)
            generator.n = 3.0
        # down
        elif self.symbol == 'DOWN15':  # close is 25 to 15 = 25 - x
            generator = LinearGenerator(periods, end_time, 24.5, interval)
            generator.slope = -1.0
        elif self.symbol == 'DOWN20':  # close is 20 to 40 = 40 - 2 * x
            generator = LinearGenerator(periods, end_time, 39.5, interval)
            generator.slope = -2.0
        elif self.symbol == 'DOWN25':  # close is 125 to 25 = 125 - x ^ 2
            generator = LinearGenerator(periods, end_time, 124.5, interval)
            generator.slope = -1.0
            generator.n = 2.0
        elif self.symbol == 'DOWN30':  # close is 30 to 130 = 1000 - x ^ 3
            generator = LinearGenerator(periods, end_time, 1029.5, interval)
            generator.n = 3.0
        # sine - we want more samples with sine, so multiple by 4
        elif self.symbol == 'SINE15':  # close is 30 to 130 = 1000 - x ^ 3
            generator = SineGenerator(periods * samples_per_period, end_time, 15, sine_interval)
            generator.frequency = frequency
        elif self.symbol == 'SINE50':  # close is 30 to 130 = 1000 - x ^ 3
            generator = SineGenerator(periods * samples_per_period, end_time, 50, sine_interval)
            generator.frequency = frequency
            generator.amplitude = 30
        elif self.symbol == 'STEP50':
            generator = StepGenerator(periods, end_time, 50, interval)
        return generator

    def get_is_physical_currency(self):
        self.data = ['USD']
        logging.debug('Using currency {}'.format(self.base_symbol))
        return self.base_symbol in self.data

    def get_is_digital_currency(self):
        return False  # not testing with True

    def get_is_listed(self) -> bool:
        return True  # all are now stock/etf equivalent for testing

    def get_prices_response(self):
        return self.get_series_response()

    def get_digital_series_response(self):
        return self.get_series_response()


def setup_collection(symbols: List[str],
                     value_types=[ValueType.OPEN, ValueType.CLOSE, ValueType.HIGH, ValueType.LOW]):
    base_symbol: str = 'USD'
    collection: AdapterCollection = AdapterCollection()
    for symbol in symbols:
        collection.add(setup_symbol_adapter(symbol, TimeInterval.DAY, AssetType.EQUITY, base_symbol, value_types))
    collection.retrieve_all_data()
    return collection


def setup_symbol_adapter(symbol, interval: TimeInterval, asset_type: AssetType, base_symbol: str,
                         value_types: List[ValueType]):
    data_adapter: MockDataAdapter = MockDataAdapter(symbol, asset_type)
    data_adapter.value_types = value_types
    data_adapter.base_symbol = base_symbol
    data_adapter.add_argument(Argument(ArgumentType.END_TIME, datetime.now()))
    data_adapter.add_argument(Argument(ArgumentType.INTERVAL, interval))
    # data_adapter.add_arg(Argument(ArgumentType.RSI_INTERVAL, interval))
    data_adapter.add_argument(Argument(ArgumentType.RSI_PERIOD, 12.0))
    return data_adapter

# def setup_portfolio(quantities: dict[str, float]):
#     portfolio: Portfolio = Portfolio('Test Portfolio')
#     assert isinstance(portfolio, Portfolio)
#     portfolio.quantities = quantities
#     return portfolio
