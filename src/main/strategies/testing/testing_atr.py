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

'''

this is just a testing strategy to prove the sma indicator is working


'''

from datetime import datetime

from main.application.single_symbol_strategy import SingleSymbolStrategy
from main.application.value_type import ValueType
from main.indicators.action_type import ActionType
from main.indicators.atr import ATR
from main.portfolio.order import MarketOrder, OrderSide
from main.portfolio.portfolio import Portfolio


class TestingATR(SingleSymbolStrategy):

    def __init__(self, symbol: str, portfolio: Portfolio):
        super().__init__("Testing ATR", symbol, portfolio)
        self.build_price_collection()
        self.atr_short = ATR(5)
        self.atr_long = ATR(10)
        self.price_list_limit = 50
        self.price_list_closes = []

    def next_step(self, current_time: datetime) -> None:
        cash = self.portfolio.quantities[self.collection.get_base_symbol()]

        '''
        a tiny version of "golden cross" and "death cross" strategy.  
        - if a fast moving SMA is above the slow moving SMA, buy
        - if a fast moving SMA is below the slow moving SMA, sell
        
        '''

        self.price_list_closes.insert(0, self.collection.get_value(self.symbol, current_time, ValueType.CLOSE))

        if len(self.price_list_closes) > self.price_list_limit:
            self.price_list_closes.pop()

        action = self.decide()
        quantity: float = self.portfolio.quantities[self.symbol]

        if action == "sell" and quantity > 0.0:
            order = MarketOrder(self.symbol, OrderSide.SELL, quantity, current_time)
            self.portfolio.open_order(order)

        if cash > 0.0 and action == "buy":
            order = MarketOrder(self.symbol, OrderSide.BUY, cash, current_time)
            self.portfolio.open_order(order)

    def decide(self):

        # get short SMA
        short_calc = self.atr_short.calc(self.price_list_closes)

        # get long SMA
        long_calc = self.atr_long.calc(self.price_list_closes)

        if short_calc is None or long_calc is None:
            return ActionType.NOT_ENOUGH_DATA

        if short_calc > long_calc:
            return ActionType.BUY

        if short_calc <= long_calc:
            return ActionType.SELL
