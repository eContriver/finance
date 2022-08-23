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

from enum import Enum, auto


class ValueType(Enum):
    """
    Adapters have a member variable called `converters` which is a list of `Converter` objects
        See: src/main/application/converter.py
    These objects take a ValueType, a callback function, and a list of look-up strings to convert
    values from the 3rd party API end-points into the known data shape used in Finance.
    """
    # for Chain
    CONNECTION_COUNT = auto()
    BALANCE = auto()
    CHAIN_NAME = auto()
    # for Stock
    CLOSE = auto()
    OPEN = auto()
    HIGH = auto()
    LOW = auto()
    VOLUME = auto()
    MACD = auto()
    MACD_HIST = auto()
    MACD_SIGNAL = auto()
    RSI = auto()
    SMA = auto()
    BOOK = auto()
    EPS = auto()  # Reported EPS
    ESTIMATED_EPS = auto()
    SURPRISE_EPS = auto()
    SURPRISE_PERCENTAGE_EPS = auto()
    GROSS_PROFIT = auto()
    REVENUE = auto()  # Total Revenue
    CASH_FLOW = auto()  # Operating Cash Flow
    DIVIDENDS = auto()
    NET_INCOME = auto()
    ASSETS = auto()  # Total Assets
    LIABILITIES = auto()  # Total Liabilities
    SHORT_DEBT = auto()  # Short Term Debt
    LONG_DEBT = auto()  # Long Term Debt
    SHARES = auto()  # Total Outstanding Shares
    DILUTED_SHARES = auto()
    EQUITY = auto()  # Total Shareholder Equity

    def __str__(self):
        return self.as_title()

    def as_title(self):
        return self.name.replace('_', ' ').lower().title()