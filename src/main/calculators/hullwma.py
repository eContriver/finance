#  Copyright 2021-2022 eContriver LLC
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

from statistics import mean
from wma import WMA
import math

class HULLWMA:
    #Weighted Moving Average with Hull smoothing

    # when you start, declare the length of the EMA you want to be using
    def __init__(self, length):
        self.averaging_length = length
        self.WMA1 = WMA(self.averaging_length/2)
        self.WMA2 = WMA(self.averaging_length)
        self.WMASQ = WMA(math.sqrt(self.averaging_length))


    # You should be using the closing price
    #   ValueType.CLOSE
    def calc(self, prices_list):

        #plot        SMA = Average(price[-displace], length);


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
=
        '''
        First, calculate two WMAs: one with the specified number of periods and one with half the specified number of periods.

        WMA1 = WMA(n/2) of price
        WMA2 = WMA(n) of price
        
        Second, calculate the raw (non-smoothed) Hull Moving Average.
        
        Raw HMA = (2 * WMA1) - WMA2
        
        Third, smooth the raw HMA with another WMA, this one with the square root of the specified number of periods.
        
        HMA = WMA(sqrt(n)) of Raw HMA
        '''

        # price 1 is the [0] in the small_price_list
        return wma_total / total_weight
