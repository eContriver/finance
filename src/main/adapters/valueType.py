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
    Adapters have a member variable called value_type_map and it can be used to override the defaults listed below e.g.
    self.value_type_map[ValueType.DIVIDEND_PAYOUT] = "dividendsPaid"
    """
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
    REPORTED_EPS = auto()
    ESTIMATED_EPS = auto()
    SURPRISE_EPS = auto()
    SURPRISE_PERCENTAGE_EPS = auto()
    GROSS_PROFIT = auto()
    TOTAL_REVENUE = auto()
    OPERATING_CASH_FLOW = auto()
    DIVIDEND_PAYOUT = auto()
    NET_INCOME = auto()
    TOTAL_ASSETS = auto()
    TOTAL_LIABILITIES = auto()
    OUTSTANDING_SHARES = auto()
    DILUTED_SHARES = auto()
    TOTAL_SHAREHOLDER_EQUITY = auto()

    def __str__(self):
        return self.as_title()

    def as_title(self):
        return self.name.replace('_', ' ').lower().title()