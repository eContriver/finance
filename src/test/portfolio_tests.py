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

from datetime import datetime, timedelta

from main.application.adapter_collection import AdapterCollection
from main.application.value_type import ValueType
from main.portfolio.order import LimitOrder, OrderSide

from main.portfolio.portfolio import Portfolio
from test.runner_test import is_test
from test.testing_utils import setup_collection


@is_test
# @only_test
def create_portfolio():
    # adapter: DataAdapter = MockDataAdapter()
    now = datetime.now()
    ten_days_ago = now - timedelta(days=10)
    portfolio: Portfolio = Portfolio('Create Portfolio Test', {}, ten_days_ago, now)
    assert isinstance(portfolio, Portfolio)
    return True


@is_test
# @only_test
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


@is_test
# @only_test
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


@is_test
# @only_test
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


@is_test
# @only_test
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
