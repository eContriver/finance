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
from datetime import datetime

from main.adapters.third_party_adapters.alpha_vantage import AlphaVantage
from main.adapters.adapter import TimeInterval, AssetType
from main.adapters.value_type import ValueType
from main.adapters.orders.order import Order
from main.adapters.third_party_adapters.robinhood import Robinhood
from main.portfolio.order import OrderSide
from main.portfolio.portfolio import Portfolio
from main.runners.runner import Runner
from main.strategies.buy_up_sell_down_trailing import BuyUpSellDownTrailing
from main.visual.visualizer import Visualizer


class OrderRunner(Runner):
    def __init__(self):
        super().__init__()

    def start(self):
        logging.info("#### Starting order runner...")

        # SymbolCollection
        # symbol = 'AMD'
        symbol = 'ETH'
        # Portfolio
        # start_time = datetime.now() - timedelta(days=14)
        portfolio: Portfolio = Portfolio('Order Creation', {})
        # portfolio: Portfolio = Portfolio('Order Creation', {'USD': 10000.0, symbol: 0.0}, start_time, end_time)
        portfolio.start_time = None
        portfolio.end_time = None
        portfolio.base_symbol = 'USD'
        portfolio.interval = TimeInterval.WEEK
        portfolio.add_adapter_class(Robinhood)
        # portfolio.add_data_adapter_class(BinanceAdapter)
        portfolio.add_adapter_class(AlphaVantage, ValueType.OPEN)
        portfolio.add_adapter_class(AlphaVantage, ValueType.CLOSE)
        portfolio.add_adapter_class(AlphaVantage, ValueType.HIGH)
        portfolio.add_adapter_class(AlphaVantage, ValueType.LOW)
        portfolio.asset_type_overrides = {
            'ETH': AssetType.DIGITAL_CURRENCY,
            'LTC': AssetType.DIGITAL_CURRENCY
        }
        # Strategy
        # strategy = BuyAndHold(symbol, data_adapter, portfolio)
        strategy = BuyUpSellDownTrailing(symbol, portfolio, buy_up=1.025, sell_down=0.975)
        # strategy = BuyUpSellDownTrailing(symbol, portfolio, buy_up=1.05, sell_down=0.95)
        # strategy = BoundedRsi(symbol, portfolio, period=14.0, upper=60.0, lower=40.0)

        strategy.collection.symbol_handles[symbol].adapters[QueryType.SERIES].span = 'year'  # 'week'
        # strategy.collection.symbol_adapters[symbol].data_adapters[QueryType.SERIES].span = '3month'  # 'week'
        strategy.sync_portfolio_with_account()

        # script_dir = os.path.dirname(os.path.realpath(__file__))
        # strategy_date_dir = FileSystem.get_and_clean_cache_dir(
        #     os.path.join(script_dir, '..', '..', '..', '.cache', 'strategies'))
        # strategy_runner = ParallelStrategyRunner(strategy_date_dir)
        # strategy_runner.configure_strategy_logging()

        # strategy.run()

        # For ordering we want to calculate today's orders:
        logging.info('=> Calculating next orders')
        order_filter = [
            OrderSide.SELL,
            # OrderSide.BUY,
        ]
        strategy.next_step(datetime.now(), order_filter)

        # strategy_runner.add_strategy(strategy.run, (), symbol, str(strategy).replace(' ', '_'))
        # strategy_runner.add_strategy(strategy.run, (start_time, end_time), symbol, str(strategy).replace(' ', '_'))

        # success = strategy_runner.run_strategies()

        title = 'Order Creator - {} - Calculated times: {} to {} (Interval: {})'.format(
            symbol,
            portfolio.get_first_completed_time(),
            portfolio.get_last_completed_time(),
            portfolio.interval.value)
        logging.info('== {}'.format(title))
        logging.info("{:>55}:  {}  (bounding times: {} to {})".format(strategy.title,
                                                                      strategy.portfolio,
                                                                      strategy.portfolio.start_time,
                                                                      strategy.portfolio.end_time))
        draw = True
        # draw = False
        if draw:
            visualizer: Visualizer = Visualizer(str(strategy), strategy.collection, [strategy.portfolio])
            visualizer.annotate_canceled_orders = True
            visualizer.annotate_opened_orders = True
            visualizer.plot_all()

        logging.info('-> Existing open orders')
        order_adapter: Order = strategy.collection.symbol_handles[symbol].adapters[QueryType.ORDERING]
        existing_orders = order_adapter.get_open_orders()
        if not existing_orders:
            logging.info('<none>')
        else:
            for order in existing_orders:
                logging.info(order)

        if strategy.portfolio.open_orders:
            logging.info('-> Orders generated by strategy')
            for order in strategy.portfolio.open_orders:
                logging.info(order)
            logging.info('-> Placing orders')
            strategy.place_open_orders()
        else:
            logging.info('-> No remaining open orders')

        return True
