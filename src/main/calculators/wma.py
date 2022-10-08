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

from main.application.calculator import Calculator


class WMA(Calculator):
    # Weighted Moving Average

    # when you start, declare the length of the EMA you want to be using
    def __init__(self, length):
        self.averaging_length = length

    # You should be using the closing price
    #   ValueType.CLOSE
    def calc(self, prices_list):

        # plot        SMA = Average(price[-displace], length);

        if not prices_list:
            # print an error?
            return None

        if len(prices_list) < self.averaging_length:
            # print an error?

            # should we still do the SMA with the little data we have?
            return None

        # should make sure prices_list is only the last "self.averaging_length" elements
        #   might want a common "price_list trim" function?

        # most recent prices are guaranteed to be at the start of the list

        small_price_list = []

        for price in prices_list:

            small_price_list.append(price)

            if len(small_price_list) >= self.averaging_length:
                break

        wma_total = 0
        wma_weight = self.averaging_length
        position = 0
        total_weight = 0

        while wma_weight > 0:
            if position > len(small_price_list):
                break
            price = small_price_list[position]
            wma_total += price * wma_weight
            total_weight += wma_weight
            wma_weight -= 1
            position += 1

        '''
        WMA = (P1 * 5) + (P2 * 4) + (P3 * 3) + (P4 * 2) + (P5 * 1) / (5 + 4+ 3 + 2 + 1)

        Where:  
        P1 = current price  
        P2 = price one bar ago, etc…
        '''

        # price 1 is the [0] in the small_price_list
        return wma_total / total_weight
