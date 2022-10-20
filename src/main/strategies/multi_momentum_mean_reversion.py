# ------------------------------------------------------------------------------
#  Copyright 2022 eContriver LLC
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

from typing import List

from main.application.time_interval import TimeInterval
from main.application.value_type import ValueType
from main.portfolio.order import OrderSide, MarketOrder
from main.portfolio.portfolio import Portfolio, get_current_value
from main.application.multi_symbol_strategy import MultiSymbolStrategy

SPY = "SPY"
TQQQ = "TQQQ"
UVXY = "UVXY"

class MultiMomentumMeanReversion(MultiSymbolStrategy):
    rsi_period: float
    sma_period: float

    def __init__(self, symbols: List[str], portfolio: Portfolio): # , sma_period: float, rsi_period: float):
        # TODO: overriding lots of variables and symbols here as this doesn't use the config file
        symbols = [SPY, TQQQ, UVXY]
        sma_period = 200.
        rsi_period = 10.
        portfolio.interval = TimeInterval.DAY
        super().__init__("Momentum Mean Reversion with SMA period {} and RSI period {}".format(sma_period, rsi_period), symbols, portfolio)
        self.sma_period = sma_period
        self.rsi_period = rsi_period
        self.build_price_collection_direct(self.symbols)
        self.build_sma_collection_direct(self.symbols, self.sma_period)
        self.build_rsi_collection(self.rsi_period)

    def next_step(self, current_time):
        """
        :param current_time: this incremental steps time
        :return:
        """
        last_time = self.portfolio.get_last_completed_time()
        # we use last time here because we can only get information about the past... if this is first step, then use now
        last_time = current_time if last_time is None else last_time

        spy_sma = self.collection.get_value(SPY, last_time, ValueType.SMA)
        spy_price = self.collection.get_value(SPY, last_time, ValueType.CLOSE)
        tqqq_rsi = self.collection.get_value(TQQQ, last_time, ValueType.RSI)
        if spy_price > spy_sma:
            if tqqq_rsi > 79.:
                self.equal_weight([UVXY], last_time, current_time)
            else:
                self.equal_weight([TQQQ], last_time, current_time)
        else:
            if tqqq_rsi > 79.:
                self.equal_weight([SPY], last_time, current_time)
            else:
                self.equal_weight([TQQQ], last_time, current_time)

    def equal_weight(self, symbols: List[str], last_time: datetime, current_time: datetime):
        value_type = ValueType.CLOSE
        for symbol in self.symbols:
            quantity: float = self.portfolio.quantities[symbol]
            if quantity > 0.0:
                self.open_sell(symbol, current_time, quantity, value_type)
        weighted = self.portfolio.quantities[self.portfolio.base_symbol] / len(symbols)
        if weighted > 0.0:
            for symbol in symbols:
                self.open_buy(symbol, current_time, weighted, value_type)

    def open_sell(self, symbol: str, current_time: datetime, quantity: float, value_type: ValueType):
        order = MarketOrder(symbol, OrderSide.SELL, quantity, current_time, value_type)
        order.message = "selling {:0.2f} {}".format(quantity, symbol)
        self.portfolio.open_order(order)

    def open_buy(self, symbol: str, current_time: datetime, quantity: float, value_type: ValueType):
        order = MarketOrder(symbol, OrderSide.BUY, quantity, current_time, value_type)
        order.message = "buying {:0.2f} {}".format(quantity, symbol)
        self.portfolio.open_order(order)
