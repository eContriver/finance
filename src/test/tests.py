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

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List

import pandas

from main.adapters.thirdPartyShims.alphaVantage import AlphaVantage
from main.common.fileSystem import FileSystem
from main.adapters.adapter import AssetType, TimeInterval, Adapter
from main.adapters.valueType import ValueType
from main.portfolio.order import OrderSide, LimitOrder
from main.portfolio.portfolio import Portfolio
from main.adapters.adapterCollection import AdapterCollection
from main.strategies.boundedRsi import BoundedRsi
from main.strategies.buyAndHold import BuyAndHold
from main.strategies.buyDownSellUp import BuyDownSellUp
from main.strategies.buyDownSellUpTrailing import BuyDownSellUpTrailing
from main.strategies.buyUpSellDownTrailing import BuyUpSellDownTrailing
from main.strategies.lastBounce import LastBounce
from main.strategies.strategy import Strategy
from main.visual.visualizer import Visualizer
from test.testExecutor import TestExecutor
from test.testUtils import setup_collection, MockDataAdapter

script_dir = os.path.dirname(os.path.realpath(__file__))
test_date_dir = FileSystem.get_and_clean_cache_dir(os.path.join(script_dir, '..', '..', '.cache', 'tests'))
test_runner = TestExecutor(test_date_dir)


# @TestExecutor.only_test
@TestExecutor.is_test(should_run=test_runner.run_gui_tests)
def create_visualization_just_collection():
    collection: AdapterCollection = setup_collection(['SINE15'],
                                                     [ValueType.OPEN, ValueType.CLOSE, ValueType.HIGH, ValueType.LOW,
                                                      ValueType.RSI])
    visualizer: Visualizer = Visualizer('All Plots', collection)
    visualizer.plot_all(block=test_runner.ui_tests_block)
    # TODO: Add image checks
    # https://matplotlib.org/3.1.0/api/testing_api.html#module-matplotlib.testing.exceptions
    # visualizer.savefig(testOutputDir + '/' + __name__ + '.png')
    # expected = testResourceDir + '/' + __name__ + '.png'
    # matplotlib.testing.compare.compare_images(expected, actual, 0.001)
    return True


# @TestExecutor.only_test
@TestExecutor.is_test(should_run=test_runner.run_gui_tests)
def create_visualization_with_portfolio():
    collection: AdapterCollection = setup_collection(['UP15', 'UP20'])
    portfolio: Portfolio = Portfolio("Test", {'USD': 0.0, 'UP15': 1.0, 'UP20': 1.0})
    portfolio.set_remaining_times(collection)
    portfolio.run_to(collection, collection.get_end_time('UP15', ValueType.CLOSE))
    visualizer: Visualizer = Visualizer('All Plots', collection, [portfolio])
    visualizer.plot_all(block=test_runner.ui_tests_block)
    return True


# @TestExecutor.only_test
@TestExecutor.is_test(should_run=test_runner.run_gui_tests)
def verify_bounded_rsi_strategy():
    symbol = 'SINE50'
    portfolio: Portfolio = Portfolio("Test", {'USD': 1000.0, symbol: 0.0})
    portfolio.add_adapter_class(MockDataAdapter)
    strategy: Strategy = BoundedRsi(symbol, portfolio, 14, 70, 30)
    strategy.run()
    visualizer: Visualizer = Visualizer('All Plots', strategy.collection, [portfolio])
    visualizer.plot_all(block=test_runner.ui_tests_block)
    return True


# @TestExecutor.only_test
@TestExecutor.is_test
def verify_common_end():
    adapter: Adapter = Adapter('TEST', AssetType.DIGITAL_CURRENCY)
    adapter.data = pandas.DataFrame()
    common_time = datetime(year=3000, month=2, day=1)
    adapter.data.loc[common_time - timedelta(weeks=1), ValueType.OPEN] = 1.0
    adapter.data.loc[common_time, ValueType.OPEN] = 1.0
    adapter.data.loc[common_time - timedelta(weeks=1), ValueType.CLOSE] = 1.0
    adapter.data.loc[common_time, ValueType.CLOSE] = 1.0
    adapter.data.loc[common_time + timedelta(weeks=1), ValueType.CLOSE] = 1.0
    assert adapter.get_common_end_time() == common_time, f"Did not get the correct common end time, expected {common_time}, received {adapter.get_common_end_time()}"
    return True


# @TestExecutor.only_test
@TestExecutor.is_test
def verify_find_closest_instance_after():
    adapter: Adapter = Adapter('TEST', AssetType.DIGITAL_CURRENCY)
    adapter.data = pandas.DataFrame()
    common_time = datetime(year=3000, month=2, day=1)
    adapter.data.loc[common_time - timedelta(weeks=2), ValueType.CLOSE] = 1.0
    adapter.data.loc[common_time, ValueType.CLOSE] = 1.0
    adapter.data.loc[common_time + timedelta(weeks=2), ValueType.CLOSE] = 1.0
    assert adapter.find_closest_instance_after(common_time) == common_time, f"Did not get the correct common end time, expected {common_time}, received {adapter.get_common_end_time()}"
    return True

# @TestExecutor.only_test
@TestExecutor.is_test
def verify_find_closest_instance_before():
    adapter: Adapter = Adapter('TEST', AssetType.DIGITAL_CURRENCY)
    adapter.data = pandas.DataFrame()
    common_time = datetime(year=3000, month=2, day=1)
    adapter.data.loc[common_time - timedelta(weeks=2), ValueType.CLOSE] = 1.0
    adapter.data.loc[common_time, ValueType.CLOSE] = 1.0
    adapter.data.loc[common_time + timedelta(weeks=2), ValueType.CLOSE] = 1.0
    assert adapter.find_closest_instance_before(common_time) == common_time, f"Did not get the correct common end time, expected {common_time}, received {adapter.get_common_end_time()}"
    return True

# @TestExecutor.only_test
@TestExecutor.is_test
def verify_find_closest_instance_after_mismatch():
    adapter: Adapter = Adapter('TEST', AssetType.DIGITAL_CURRENCY)
    adapter.data = pandas.DataFrame()
    common_time = datetime(year=3000, month=2, day=1)
    mismatch_time = common_time - timedelta(weeks=1)
    adapter.data.loc[common_time - timedelta(weeks=2), ValueType.CLOSE] = 1.0
    adapter.data.loc[common_time, ValueType.CLOSE] = 1.0
    adapter.data.loc[common_time + timedelta(weeks=2), ValueType.CLOSE] = 1.0
    assert adapter.find_closest_instance_after(mismatch_time) == common_time, f"Did not get the correct common end time, expected {common_time}, received {adapter.get_common_end_time()}"
    return True

# @TestExecutor.only_test
@TestExecutor.is_test
def verify_find_closest_instance_before_mismatch():
    adapter: Adapter = Adapter('TEST', AssetType.DIGITAL_CURRENCY)
    adapter.data = pandas.DataFrame()
    common_time = datetime(year=3000, month=2, day=1)
    mismatch_time = common_time + timedelta(weeks=1)
    adapter.data.loc[common_time - timedelta(weeks=2), ValueType.CLOSE] = 1.0
    adapter.data.loc[common_time, ValueType.CLOSE] = 1.0
    adapter.data.loc[common_time + timedelta(weeks=2), ValueType.CLOSE] = 1.0
    assert adapter.find_closest_instance_before(mismatch_time) == common_time, f"Did not get the correct common end time, expected {common_time}, received {adapter.get_common_end_time()}"
    return True

# @TestExecutor.only_test
@TestExecutor.is_test
def verify_common_start():
    adapter: Adapter = Adapter('TEST', AssetType.DIGITAL_CURRENCY)
    adapter.data = pandas.DataFrame()
    common_time = datetime(year=3000, month=2, day=1)
    adapter.data.loc[common_time, ValueType.OPEN] = 1.0
    adapter.data.loc[common_time + timedelta(weeks=1), ValueType.OPEN] = 1.0
    adapter.data.loc[common_time - timedelta(weeks=1), ValueType.CLOSE] = 1.0
    adapter.data.loc[common_time, ValueType.CLOSE] = 1.0
    adapter.data.loc[common_time + timedelta(weeks=1), ValueType.CLOSE] = 1.0
    assert adapter.get_common_start_time() == common_time, f"Did not get the correct common end time, expected {common_time}, received {adapter.get_common_end_time()}"
    return True


# @TestExecutor.only_test
@TestExecutor.is_test
def verify_last_bounce_strategy():
    symbol = 'STEP50'
    portfolio: Portfolio = Portfolio("Test", {'USD': 1000.0, symbol: 0.0})
    portfolio.add_adapter_class(MockDataAdapter)
    strategy: Strategy = LastBounce(symbol, portfolio, 0.5, 0.01)
    strategy.run()
    # visualizer: Visualizer = Visualizer('All Plots', strategy.collection, [portfolio])
    # visualizer.annotate_opened_orders = True
    # visualizer.plot_all()
    start_value = round(portfolio.data.iloc[0, 0], 2)
    assert start_value == 1000.00, "start_value is wrong: {}".format(start_value)
    before_buy_value = round(portfolio.data.iloc[5, 0], 2)
    assert before_buy_value == 1000.0, "before_buy_value is wrong: {}".format(before_buy_value)
    after_buy_value = round(portfolio.data.iloc[7, 0], 2)
    assert after_buy_value == 1034.51, "after_buy_value is wrong: {}".format(after_buy_value)
    end_value = round(portfolio.data.iloc[-1, 0], 2)
    assert end_value == 1051.95, "end_value is wrong: {}".format(end_value)
    return True


# @TestExecutor.only_test
@TestExecutor.is_test
def verify_buy_up_sell_down_trailing_strategy():
    symbol = 'SINE50'
    portfolio: Portfolio = Portfolio("Test", {'USD': 1000.0, symbol: 0.0})
    portfolio.add_adapter_class(MockDataAdapter)
    strategy: Strategy = BuyUpSellDownTrailing(symbol, portfolio, 1.1, 0.9)
    strategy.run()
    # visualizer: Visualizer = Visualizer('All Plots', strategy.collection, [portfolio])
    # visualizer.annotate_opened_orders = True
    # visualizer.plot_all()
    start_value = round(portfolio.data.iloc[0, 0], 2)
    assert start_value == 1000.00, "start_value is wrong: {}".format(start_value)
    after_buy_value = round(portfolio.data.iloc[9, 0], 2)
    assert after_buy_value == 1478.62, "after_buy_value is wrong: {}".format(after_buy_value)
    end_value = round(portfolio.data.iloc[-1, 0], 2)
    assert end_value == 9951.62, "end_value is wrong: {}".format(end_value)
    return True


# @TestExecutor.only_test
@TestExecutor.is_test
def verify_buy_down_sell_up_trailing_strategy():
    symbol = 'SINE50'
    portfolio: Portfolio = Portfolio("Test", {'USD': 1000.0, symbol: 0.0})
    portfolio.add_adapter_class(MockDataAdapter)
    strategy: Strategy = BuyDownSellUpTrailing(symbol, portfolio, 0.9, 1.1)
    strategy.run()
    # visualizer: Visualizer = Visualizer('All Plots', strategy.collection, [portfolio])
    # visualizer.annotate_opened_orders = True
    # visualizer.plot_all()
    start_value = round(portfolio.data.iloc[0, 0], 2)
    assert start_value == 1000.00, "start_value is wrong: {}".format(start_value)
    after_buy_value = round(portfolio.data.iloc[15, 0], 2)
    assert after_buy_value == 979.23, "after_buy_value is wrong: {}".format(after_buy_value)
    end_value = round(portfolio.data.iloc[-1, 0], 2)
    assert end_value == 83.76, "end_value is wrong: {}".format(end_value)
    return True


# @TestExecutor.only_test
@TestExecutor.is_test
def verify_buy_down_sell_up_next_day_strategy():
    symbol = 'UP15'
    portfolio: Portfolio = Portfolio("Test", {'USD': 1000.0, symbol: 0.0})
    portfolio.add_adapter_class(MockDataAdapter)
    strategy: Strategy = BuyDownSellUp(symbol, portfolio, 0.95, 1.5)
    strategy.run()
    # visualizer: Visualizer = Visualizer('All Plots', strategy.collection, [portfolio])
    # visualizer.annotate_opened_orders = True
    # visualizer.plot_all()
    start_value = round(portfolio.data.iloc[0, 0], 2)
    assert start_value == 1000.00, "start_value is wrong: {}".format(start_value)
    # assert start_value == 1018.68, "start_value is wrong: {}".format(start_value)
    on_buy_value = round(portfolio.data.iloc[1, 0], 2)
    # open limit buy order is set first day for 14.725 (0.95 * high) on_buy day low is 14.5 so purchase is done at
    # 14.725
    # 1000 / 14.725 -> 67.911 shares and close is 16.0, 16.0 * 67.911 -> 1086.59 (with some rounding)
    assert on_buy_value == 1086.59, "on_buy_value is wrong: {}".format(on_buy_value)
    before_sale_value = round(portfolio.data.iloc[4, 0], 2)
    # y = change/day * days * shares + 1086.59 -> 1.0 * 5 * 67.911 -> 339.555 + 1086.59 -> 1426.145
    assert before_sale_value == 1290.32, "before_sale_value is wrong: {}".format(before_sale_value)
    on_sale_value = round(portfolio.data.iloc[5, 0], 2)
    # sell should be set at 1.5 * 14.5 low (times[1]) = 21.75
    # sell 67.911 shares at 21.75 / share = 1477.086
    assert on_sale_value == 1358.23, "on_sale_value is wrong: {}".format(on_sale_value)
    end_value = round(portfolio.data.iloc[-1, 0], 2)
    assert end_value == 1477.08, "end_value is wrong: {}".format(end_value)
    return True


# @TestExecutor.only_test
@TestExecutor.is_test
def verify_buy_down_sell_up_strategy():
    symbol = 'UP15'
    portfolio: Portfolio = Portfolio("Test", {'USD': 0.0, symbol: 100.0})
    portfolio.add_adapter_class(MockDataAdapter)
    strategy: Strategy = BuyDownSellUp(symbol, portfolio, 0.9, 1.1)
    strategy.run()
    times = sorted(portfolio.data.keys())
    # visualizer: Visualizer = Visualizer('All Plots', collection, [portfolio])
    # visualizer.plot_all()
    start_value = round(portfolio.data.iloc[0, 0], 2)
    # start 15.00 close * 100 shares:
    assert start_value == 1500.00, "start_value is wrong: {}".format(start_value)
    on_sale_value = round(portfolio.data.iloc[1, 0], 2)
    # sell 100 shares if prices goes to 1.1 * 13.5 low = 14.85
    assert on_sale_value == 1485.0, "on_sale_value is wrong: {}".format(on_sale_value)
    end_value = round(portfolio.data.iloc[-1, 0], 2)
    assert end_value == 1485.0, "end_value is wrong: {}".format(end_value)
    return True


# @TestExecutor.only_test
@TestExecutor.is_test
def verify_buy_and_hold_strategy():
    symbol = 'UP15'
    portfolio: Portfolio = Portfolio("Test", {'USD': 1000.0, symbol: 0.0})
    portfolio.add_adapter_class(MockDataAdapter)
    strategy: Strategy = BuyAndHold(symbol, portfolio)
    strategy.run()
    # visualizer: Visualizer = Visualizer('All Plots', strategy.collection, [portfolio])
    # visualizer.plot_all()
    times = sorted(portfolio.data.keys())
    start_value = round(portfolio.data.iloc[0, 0], 2)
    assert start_value == 1000.0, "start_value is wrong: {}".format(start_value)
    next_value = round(portfolio.data.iloc[1, 0], 2)
    assert next_value == 1066.67, "next_value is wrong: {}".format(next_value)
    end_value = round(portfolio.data.iloc[-1, 0], 2)
    assert end_value == 2266.67, "end_value is wrong: {}".format(end_value)
    return True


# @TestExecutor.only_test
@TestExecutor.is_test
def verify_portfolio_limit_buy():
    symbol = 'DOWN15'
    collection: AdapterCollection = setup_collection([symbol])
    portfolio: Portfolio = Portfolio("Test", {'USD': 25.0, symbol: 0.0})
    portfolio.set_remaining_times(collection)
    end_time = collection.get_end_time(symbol, ValueType.CLOSE)
    mid = end_time - timedelta(days=5)
    mid_plus_one = mid + timedelta(days=1)
    portfolio.run_to(collection, mid)
    price = collection.get_value(symbol, portfolio.get_last_completed_time(), ValueType.LOW)
    limit_price = price * 0.9
    quantity = portfolio.quantities['USD']  # TODO: baseCurrency
    order = LimitOrder(symbol, OrderSide.BUY, limit_price, quantity, mid)
    portfolio.open_order(order)
    portfolio.run_to(collection, end_time)
    # visualizer: Visualizer = Visualizer('All Plots', collection, [portfolio])
    # visualizer.annotate_opened_orders = True
    # visualizer.plot_all(block=False)
    start_value = portfolio.data.iloc[0, 0]
    assert start_value == 25.0, "start_value is wrong: {}".format(start_value)
    mid_value = list(portfolio.data.loc[mid, :])[0]
    assert mid_value == 25.0, "mid_value is wrong: {}".format(mid_value)
    mid_plus_one_value = round(list(portfolio.data.loc[mid_plus_one, :])[0], 2)
    assert mid_plus_one_value == 26.32, "mid_plus_one_value is wrong: {}".format(mid_plus_one_value)
    end_value = round(portfolio.data.iloc[-1, 0], 2)
    assert end_value == 14.62, "end_value is wrong: {}".format(end_value)
    return True


# @TestExecutor.only_test
@TestExecutor.is_test
def verify_portfolio_limit_sell():
    symbol = 'UP15'
    collection: AdapterCollection = setup_collection([symbol])
    portfolio: Portfolio = Portfolio("Test", {'USD': 0.0, symbol: 1.0})
    portfolio.set_remaining_times(collection)
    end_time = collection.get_end_time(symbol, ValueType.CLOSE)
    mid = end_time - timedelta(days=5)
    mid_plus_one = mid + timedelta(days=1)
    portfolio.run_to(collection, mid)
    price = collection.get_value(symbol, portfolio.get_last_completed_time(), ValueType.HIGH)
    limit_price = price * 1.1
    quantity = portfolio.quantities[symbol]
    order = LimitOrder(symbol, OrderSide.SELL, limit_price, quantity, mid)
    portfolio.open_order(order)
    portfolio.run_to(collection, end_time)
    # visualizer: Visualizer = Visualizer('All Plots', collection, [portfolio])
    # visualizer.plotAll()
    # times = sorted(portfolio.value_data.keys())
    start_value = portfolio.data.iloc[0, 0]
    assert start_value == 15.0, "start_value is wrong: {}".format(start_value)
    mid_value = list(portfolio.data.loc[mid, :])[0]
    assert mid_value == 29.0, "mid_value is wrong: {}".format(mid_value)
    mid_plus_one_value = list(portfolio.data.loc[mid_plus_one, :])[0]
    assert mid_plus_one_value == 30.0, "mid_plus_one_value is wrong: {}".format(mid_plus_one_value)
    end_value = portfolio.data.iloc[-1, 0]
    assert end_value == 32.45, "end_value is wrong: {}".format(end_value)
    return True


# @TestExecutor.only_test
@TestExecutor.is_test
def verify_get_remaining_times():
    collection: AdapterCollection = setup_collection(['UP15'])
    start_time = collection.get_common_start_time()
    assert start_time is not None
    portfolio: Portfolio = Portfolio("Test", {'USD': 0.0, 'UP15': 1.0})
    portfolio.set_remaining_times(collection)
    last_time = portfolio.get_last_completed_time()
    assert last_time is None
    portfolio.run_to(collection, collection.get_common_start_time())
    last_time = portfolio.get_last_completed_time()
    assert last_time == start_time, "Last time {} and start time {} do not match".format(last_time, start_time)
    remaining_times = portfolio.get_remaining_times()
    assert len(remaining_times) == 19, "the size is wrong: {}".format(len(remaining_times))
    return True


# @TestExecutor.only_test
@TestExecutor.is_test
def verify_portfolio_run_to():
    collection: AdapterCollection = setup_collection(['UP15', 'UP20'])
    portfolio: Portfolio = Portfolio("Test", {'USD': 0.0, 'UP15': 1.0, 'UP20': 1.0})
    portfolio.set_remaining_times(collection)
    symbol = 'UP15'
    portfolio.run_to(collection, collection.get_end_time(symbol, ValueType.CLOSE))
    # times = sorted(portfolio.value_data.keys())
    start_value = portfolio.data.iloc[0, 0]
    assert start_value == 35.0, "start_value is wrong: {}".format(start_value)
    end_value = portfolio.data.iloc[-1, 0]
    assert end_value == 90.0, "end_value is wrong: {}".format(end_value)
    return True


# @TestExecutor.only_test
@TestExecutor.is_test
def verify_data_reading():
    collection: AdapterCollection = setup_collection(['UP15', 'UP20'])
    symbol: str = 'UP15'
    end_time: datetime = collection.get_end_time(symbol, ValueType.CLOSE)
    values: pandas.Series = collection.get_instance_values(symbol, end_time, ValueType.CLOSE)
    assert values[ValueType.CLOSE] == 34.0, "close data is wrong - received: {}".format(values[ValueType.CLOSE])
    close: float = collection.get_value(symbol, end_time, ValueType.CLOSE)
    assert close == 34.0, "close data is wrong - received: {}".format(close)
    return True


# @TestExecutor.only_test
# @TestExecutor.is_test
def adding_new_data_adapters():
    """
    This test should not be enabled normally, but can be used to test a data adapter as it is added.
    We don't want this running regularly, because it would have to communicate with external sites every run.
    """
    base_symbol: str = 'USD'
    collection: AdapterCollection = AdapterCollection(base_symbol)
    symbols: List[str] = ['NVDA']
    asset_type: AssetType = AssetType.EQUITY
    # 1:
    query_type_types = [
        # QueryType.CASH_FLOW
        QueryType.BALANCE_SHEET
    ]
    # 2:
    value_types = [ValueType.TOTAL_ASSETS]
    # 3:
    interval = TimeInterval.QUARTER
    # 4:
    data_adapters = [
        # YahooAdapter,
        AlphaVantage
    ]
    for symbol in symbols:
        for data_adapter_ctor in data_adapters:
            data_adapter: Adapter = data_adapter_ctor(symbol, base_symbol)
            data_adapter.asset_type = asset_type
            symbol_handle: AdapterCollection = AdapterCollection(symbol)
            for query_type in query_type_types:  # QueryType:
                # 5: Add parameters
                data_adapter.balance_sheet_interval = interval
                symbol_handle.adapters[query_type] = data_adapter
            collection.add_symbol_handle(symbol_handle)

    collection.retrieve_all_data()

    for symbol in symbols:
        symbol_handle: AdapterCollection = collection.get_symbol_handle(symbol)
        end_time: datetime = symbol_handle.get_end_time(symbol)
        assert end_time is not None, "The end time is {} (None) we will stop testing now.".format(end_time)
        # if end_time is None:
        #     logging.warning("The end time is {} (None) we will skip reporting values.".format(end_time))
        #     break
        for value_type in value_types:
            value: float = symbol_handle.get_value(symbol, end_time, ValueType.CLOSE)
            logging.info("Value for {} is: {}".format(value_type, value))
        # assert close == 34.0, "close data is wrong - received: {}".format(close)

    return True


# @TestExecutor.only_test
@TestExecutor.is_test
def create_portfolio():
    # adapter: DataAdapter = MockDataAdapter()
    now = datetime.now()
    ten_days_ago = now - timedelta(days=10)
    portfolio: Portfolio = Portfolio('Create Portfolio Test', {}, ten_days_ago, now)
    assert isinstance(portfolio, Portfolio)
    return True


def test_launcher():
    for run_test in TestExecutor.tests_to_run:
        if not TestExecutor.run_only_tests or (run_test in TestExecutor.run_only_tests):
            test_runner.add_test(globals()[run_test], ())
    passed = test_runner.start()
    return passed
