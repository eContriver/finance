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

from main.adapters.adapterCollection import AdapterCollection
from main.adapters.valueType import ValueType
from main.portfolio.portfolio import Portfolio
from main.strategies.boundedRsi import BoundedRsi
from main.strategies.strategy import Strategy
from main.visual.visualizer import Visualizer
from test.testExecutor import is_test, TestRunner
from test.testUtils import setup_collection, MockDataAdapter


@is_test(should_run=TestRunner.get_instance().run_gui_tests)
def create_visualization_just_collection():
    collection: AdapterCollection = setup_collection(['SINE15'],
                                                     [ValueType.OPEN, ValueType.CLOSE, ValueType.HIGH, ValueType.LOW,
                                                      ValueType.RSI])
    visualizer: Visualizer = Visualizer('All Plots', collection)
    visualizer.plot_all(block=TestRunner.get_instance().ui_tests_block)
    # TODO: Add image checks
    # https://matplotlib.org/3.1.0/api/testing_api.html#module-matplotlib.testing.exceptions
    # visualizer.savefig(testOutputDir + '/' + __name__ + '.png')
    # expected = testResourceDir + '/' + __name__ + '.png'
    # matplotlib.testing.compare.compare_images(expected, actual, 0.001)
    return True


@is_test(should_run=TestRunner.get_instance().run_gui_tests)
def create_visualization_with_portfolio():
    collection: AdapterCollection = setup_collection(['UP15', 'UP20'])
    portfolio: Portfolio = Portfolio("Test", {'USD': 0.0, 'UP15': 1.0, 'UP20': 1.0})
    portfolio.set_remaining_times(collection)
    portfolio.run_to(collection, collection.get_end_time('UP15', ValueType.CLOSE))
    visualizer: Visualizer = Visualizer('All Plots', collection, [portfolio])
    visualizer.plot_all(block=TestRunner.get_instance().ui_tests_block)
    return True


@is_test(should_run=TestRunner.get_instance().run_gui_tests)
def verify_bounded_rsi_strategy():
    symbol = 'SINE50'
    portfolio: Portfolio = Portfolio("Test", {'USD': 1000.0, symbol: 0.0})
    portfolio.add_adapter_class(MockDataAdapter)
    strategy: Strategy = BoundedRsi(symbol, portfolio, 14, 70, 30)
    strategy.run()
    visualizer: Visualizer = Visualizer('All Plots', strategy.collection, [portfolio])
    visualizer.plot_all(block=TestRunner.get_instance().ui_tests_block)
    return True