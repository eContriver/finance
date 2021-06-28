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

from typing import List

from main.portfolio.portfolio import Portfolio
from main.strategies.strategy import Strategy


class MultiSymbolStrategy(Strategy):
    symbol: List[str]

    def __init__(self, title: str, symbols: List[str], portfolio: Portfolio):
        super().__init__(title, portfolio)
        self.symbols = symbols

    def __str__(self):
        string = " ".join(self.symbols) + " " + self.title
        string += "" if self.portfolio.start_time is None else " starting {}".format(self.portfolio.start_time)
        string += "" if self.portfolio.end_time is None else " ending {}".format(self.portfolio.end_time)
        return string

    def build_series_collection(self):
        assert self.collection is None
        builder = CollectionBuilder(self.symbols)
        builder.add_series_adapter_coln(
            self.portfolio.get_adapter_class(QueryType.SERIES),
            self.portfolio.base_symbol,
            self.portfolio.interval,
            self.portfolio.asset_type_overrides
        )
        builder.add_order_adapter_coln(
            self.portfolio.get_adapter_class(QueryType.ORDERING),
            self.portfolio.base_symbol,
            self.portfolio.asset_type_overrides
        )
        self.collection = builder.build_coln(self.portfolio.base_symbol)

    def build_macd_collection(self, slow, fast, signal):
        assert self.collection is None
        builder = CollectionBuilder(self.symbols)
        builder.add_series_adapter_coln(
            self.portfolio.get_adapter_class(QueryType.SERIES),
            self.portfolio.base_symbol,
            self.portfolio.interval,
            self.portfolio.asset_type_overrides
        )
        builder.add_order_adapter_coln(
            self.portfolio.get_adapter_class(QueryType.ORDERING),
            self.portfolio.base_symbol,
            self.portfolio.asset_type_overrides
        )
        builder.add_macd_adapter_coln(
            self.portfolio.get_adapter_class(QueryType.MACD),
            self.portfolio.base_symbol,
            self.portfolio.interval,
            self.portfolio.asset_type_overrides,
            slow, fast, signal
        )
        self.collection = builder.build_coln(self.portfolio.base_symbol)

    def build_rsi_collection(self, period):
        assert self.collection is None
        builder = CollectionBuilder(self.symbols)
        builder.add_series_adapter_coln(
            self.portfolio.get_adapter_class(QueryType.SERIES),
            self.portfolio.base_symbol,
            self.portfolio.interval,
            self.portfolio.asset_type_overrides
        )
        builder.add_order_adapter_coln(
            self.portfolio.get_adapter_class(QueryType.ORDERING),
            self.portfolio.base_symbol,
            self.portfolio.asset_type_overrides
        )
        builder.add_rsi_adapter_coln(
            self.portfolio.get_adapter_class(QueryType.RSI),
            self.portfolio.base_symbol,
            self.portfolio.interval,
            self.portfolio.asset_type_overrides,
            period
        )
        self.collection = builder.build_coln(self.portfolio.base_symbol)

    def build_sma_collection(self, period):
        assert self.collection is None
        builder = CollectionBuilder(self.symbols)
        builder.add_series_adapter_coln(
            self.portfolio.get_adapter_class(QueryType.SERIES),
            self.portfolio.base_symbol,
            self.portfolio.interval,
            self.portfolio.asset_type_overrides
        )
        builder.add_order_adapter_coln(
            self.portfolio.get_adapter_class(QueryType.ORDERING),
            self.portfolio.base_symbol,
            self.portfolio.asset_type_overrides
        )
        builder.add_sma_adapter_coln(
            self.portfolio.get_adapter_class(QueryType.SMA),
            self.portfolio.base_symbol,
            self.portfolio.interval,
            self.portfolio.asset_type_overrides,
            period
        )
        self.collection = builder.build_coln(self.portfolio.base_symbol)

    def build_book_collection(self, period):
        assert self.collection is None
        builder = CollectionBuilder(self.symbols)
        builder.add_series_adapter_coln(
            self.portfolio.get_adapter_class(QueryType.SERIES),
            self.portfolio.base_symbol,
            self.portfolio.interval,
            self.portfolio.asset_type_overrides
        )
        builder.add_order_adapter_coln(
            self.portfolio.get_adapter_class(QueryType.ORDERING),
            self.portfolio.base_symbol,
            self.portfolio.asset_type_overrides
        )
        builder.add_book_adapter_coln(
            self.portfolio.get_adapter_class(QueryType.BOOK),
            self.portfolio.base_symbol,
            self.portfolio.interval,
            self.portfolio.asset_type_overrides,
            period
        )
        self.collection = builder.build_coln(self.portfolio.base_symbol)
