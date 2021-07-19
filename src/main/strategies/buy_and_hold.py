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


from datetime import datetime

from main.portfolio.order import MarketOrder, OrderSide
from main.portfolio.portfolio import Portfolio
from main.strategies.single_symbol_strategy import SingleSymbolStrategy


class BuyAndHold(SingleSymbolStrategy):

    def __init__(self, symbol: str, portfolio: Portfolio):
        super().__init__("Buy and Hold", symbol, portfolio)
        self.build_price_collection()

    def next_step(self, current_time: datetime) -> None:
        cash = self.portfolio.quantities[self.collection.get_base_symbol()]
        if cash > 0.0:
            order = MarketOrder(self.symbol, OrderSide.BUY, cash, current_time)
            self.portfolio.open_order(order)
