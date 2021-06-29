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

from main.portfolio.portfolio import Portfolio
from main.strategies.buyAndHold import BuyAndHold
from main.strategies.buyDownSellUp import BuyDownSellUp
from main.strategies.buyDownSellUpTrailing import BuyDownSellUpTrailing
from main.strategies.buyUpSellDownTrailing import BuyUpSellDownTrailing
from main.strategies.lastBounce import LastBounce
from main.strategies.strategy import Strategy
from test.testExecutor import is_test
from test.testUtils import MockDataAdapter


@is_test
# @only_test
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


@is_test
# @only_test
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


@is_test
# @only_test
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


@is_test
# @only_test
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


@is_test
# @only_test
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


@is_test
# @only_test
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