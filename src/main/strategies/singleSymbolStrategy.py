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
from typing import Optional

from main.portfolio.portfolio import Portfolio
from main.strategies.strategy import Strategy


class SingleSymbolStrategy(Strategy):
    symbol: Optional[str]

    def __init__(self, title: str, symbol: str, portfolio: Portfolio):
        super().__init__(title, portfolio)
        self.symbol = symbol

    def __str__(self):
        string = self.symbol + " " + self.title
        string += "" if self.portfolio.start_time is None else " starting {}".format(self.portfolio.start_time)
        string += "" if self.portfolio.end_time is None else " ending {}".format(self.portfolio.end_time)
        return string

    def build_price_collection(self, cache_key_date: Optional[datetime] = None):
        self.add_price_collection(self.symbol, cache_key_date)

    def build_macd_collection(self, slow, fast, signal, cache_key_date: Optional[datetime] = None):
        self.add_macd_collection(self.symbol, slow, fast, signal, cache_key_date)

    def build_rsi_collection(self, period, cache_key_date: Optional[datetime] = None):
        self.add_rsi_collection(self.symbol, period, cache_key_date)

    def build_book_collection(self, period, cache_key_date: Optional[datetime] = None):
        self.add_book_collection(self.symbol, period, cache_key_date)
