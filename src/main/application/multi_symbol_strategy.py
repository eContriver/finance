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
from typing import List, Optional

from main.application.strategy import Strategy
from main.portfolio.portfolio import Portfolio


class MultiSymbolStrategy(Strategy):
    symbol: List[str]

    def __init__(self, title: str, symbols: List[str], portfolio: Portfolio):
        super().__init__(title, portfolio)
        self.symbols = symbols

    def __str__(self):
        string = " ".join(self.symbols) + " " + self.title
        # string += "" if self.portfolio.start_time is None else " starting {}".format(self.portfolio.start_time)
        # string += "" if self.portfolio.end_time is None else " ending {}".format(self.portfolio.end_time)
        return string

    def build_price_collection(self, cache_key_date: Optional[datetime] = None):
        for symbol in self.symbols:
            self.add_price_collection(symbol, cache_key_date)

    def build_sma_collection(self, period, cache_key_date: Optional[datetime] = None):
        for symbol in self.symbols:
            self.add_sma_collection(symbol, period, cache_key_date)

    def build_macd_collection(self, slow, fast, signal, cache_key_date: Optional[datetime] = None):
        for symbol in self.symbols:
            self.add_macd_collection(symbol, slow, fast, signal, cache_key_date)

    def build_rsi_collection(self, period, cache_key_date: Optional[datetime] = None):
        for symbol in self.symbols:
            self.add_rsi_collection(symbol, period, cache_key_date)

    def build_book_collection(self, period, cache_key_date: Optional[datetime] = None):
        for symbol in self.symbols:
            self.add_book_collection(symbol, period, cache_key_date)
