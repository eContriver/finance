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

    Not all liabilities are debt, but all debt is a liability.

    For AlphaVantage balance_sheet example using AVGO on 8/28/2021 period: 2020-11-01...
    Assets:
            "totalAssets":                       "75933000000", 75.9b
            "totalNonCurrentAssets":             "64038000000", 64.0b
            "intangibleAssets":                  "60229000000", 60.2b
            "intangibleAssetsExcludingGoodwill": "16782000000", 16.8b
            "totalCurrentAssets":                "11895000000", 11.9b
            "otherNonCurrrentAssets":             "1300000000",  1.3b
            "otherCurrentAssets":                  "977000000",  977m
    Liabilities:
            "totalLiabilities":           "52032000000", 52.0b
            "totalNonCurrentLiabilities": "46532000000", 46.5b
            "totalCurrentLiabilities":     "6371000000",  6.4b
            "otherNonCurrentLiabilities":  "5426000000",  5.4b
            "otherCurrentLiabilities":     "3831000000",  3.8b
    Debt:
            "shortLongTermDebtTotal":     "41498000000", 41.5b
            "longTermDebt":               "40994000000", 41.0b
            "longTermDebtNoncurrent":     "40235000000", 40.2b
            "currentDebt":                  "847000000", 847m
            "currentLongTermDebt":          "827000000", 827m
            "shortTermDebt":                "504000000", 504m
    Cash:
            "cashAndCashEquivalentsAtCarryingValue": "7618000000", 7.6b

            short + long - cash = 0.504 + 40.994 - 7.618 =
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