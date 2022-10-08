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

import math

from main.application.calculator import Calculator
from main.calculators.wma import WMA


class HULLWMA(Calculator):
    """
    Weighted Moving Average with Hull smoothing
    """

    # when you start, declare the length of the EMA you want to be using
    def __init__(self, length):
        self.averaging_length = length
        self.WMA1 = WMA(self.averaging_length / 2)
        self.WMA2 = WMA(self.averaging_length)
        # python's built in 'round' function rounds decimal numbers to integers
        self.WMASQ = WMA(round(math.sqrt(self.averaging_length)))

    # You should be using the closing price
    #   ValueType.CLOSE

    def make_wma_list(self, wma_obj, prices_list, length):

        wma_list = []
        position = 0

        # we keep increasing the index into the position array
        #   we keep appending the new Weighted Moving Average onto the results array
        #   the WMA_obj knows he will always only calculate a WMA of the same length it was originally designed to
        #   finally, we return the result
        while (position + length) < len(prices_list):
            wma_list.append(wma_obj(prices_list[position:]))
            position += 1

        return wma_list

    def find_raw_wma_list(self, wma1_list, wma2_list):

        raw_wma_list = []

        # loops over them both, but quits when the smaller list is empty
        for wma1_price, wma2_price in zip(wma1_list, wma2_list):
            raw_wma_list.append((2 * wma1_price) - wma2_price)

        return raw_wma_list

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

        '''
        First, calculate two WMAs: one with the specified number of periods and one with half the specified number of periods.

        WMA1 = WMA(n/2) of price
        WMA2 = WMA(n) of price
        
        Second, calculate the raw (non-smoothed) Hull Moving Average.
        
        Raw HMA = (2 * WMA1) - WMA2
        
        Third, smooth the raw HMA with another WMA, this one with the square root of the specified number of periods.
        
        HMA = WMA(sqrt(n)) of Raw HMA
        '''

        WMA1_list = self.make_wma_list(self.WMA1, prices_list, self.averaging_length / 2)
        WMA2_list = self.make_wma_list(self.WMA2, prices_list, self.averaging_length)

        raw_wma_list = self.find_raw_wma_list(WMA1_list, WMA2_list)

        # we already defined this as having a period of round(sqrt(self.averaging length))
        hull_moving_average = self.WMASQ.calc(raw_wma_list)

        # price 1 is the [0] in the small_price_list
        return hull_moving_average
