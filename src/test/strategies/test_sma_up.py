# ------------------------------------------------------------------------------
#  Copyright 2021-2022 eContriver LLC
#  This file is part of Finance from eContriver.
#  -
#  Finance from eContriver is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  any later version.
#  -
#  Finance from eContriver is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  -
#  You should have received a copy of the GNU General Public License
#  along with Finance from eContriver.  If not, see <https://www.gnu.org/licenses/>.
# ------------------------------------------------------------------------------

from datetime import datetime
from unittest import TestCase

from main.application.strategy import Strategy
from main.application.time_interval import TimeInterval
from main.portfolio.portfolio import Portfolio
from main.strategies.sma_up import SmaUp
from test.testing_utils import MockDataAdapter


class TestSmaUpStrategy(TestCase):
    def test_sma_up_is_accurate(self):
        """
        Tests that SMA Up works as expected
        :return:
        """
        # configure_test_logging()
        symbol: str = 'SINE50'
        adapter_class = MockDataAdapter
        price_interval = TimeInterval.DAY
        end_time: datetime = datetime.now()
        end_time = datetime(end_time.year, end_time.month, end_time.day)
        start_time: datetime = end_time - (1 * TimeInterval.YEAR.timedelta)

        portfolio: Portfolio = Portfolio("Test", {'USD': 1000.0, symbol: 0.0}, start_time, end_time)
        portfolio.interval = price_interval
        portfolio.add_adapter_class(adapter_class)

        strategy: Strategy = SmaUp(symbol, portfolio, 4, 10, 20)
        strategy.run()

        # visualizer: Visualizer = Visualizer('All Plots', strategy.collection, [portfolio])
        # visualizer.plot_all()

        # TODO: what to test now?
