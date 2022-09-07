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
from ema import EMA

class MACD:

    # when you start, declare the length of the SMA you want to be using
    def __init__(self, fast_length, slow_length, macd_length):
        self.fast_length = fast_length
        self.slow_length = slow_length
        self.macd_length = macd_length

        self.fast_EMA = EMA(self.fast_length)
        self.slow_EMA = EMA(self.slow_length)
        self.average_EMA = EMA(self.macd_length)

    # You should be using the closing price
    #   ValueType.CLOSE

    def make_ema_list(self, ema_obj, prices_list, length):

        ema_list = []
        position = 0

        # we keep increasing the index into the position array
        #   we keep appending the new Weighted Moving Average onto the results array
        #   the WMA_obj knows he will always only calculate a WMA of the same length it was originally designed to
        #   finally, we return the result
        while ( position + length ) < len(prices_list):
            ema_list.append(ema_obj(prices_list[position:]))
            position += 1

        return ema_list

    def find_difference(self, fast_list, slow_list):
        """
        Value = MovingAverage(averageType, close, fastLength) - MovingAverage(averageType, close, slowLength);
        Avg = MovingAverage(averageType, Value, MACDLength);

        Diff = Value - Avg;
        """
        value_list = []
        difference_list = []

        for fast_price, slow_price in zip(fast_list, slow_list):
            value_list.append(fast_price - slow_price)

        average = self.average_EMA.calc(value_list)

        for value_price, average_price in zip(value_list, average_list):
            difference_list.append(value_price - average_price)

        return difference_list

    def calc(self, prices_list):
        # plot        SMA = Average(price[-displace], length);
        if not prices_list:
            # print an error?
            return None

        if len(prices_list) < self.slow_length:
            # print an error?
            return None

        # should make sure prices_list is only the last "self.averaging_length" elements
        #   might want a common "price_list trim" function?

        # most recent prices are guaranteed to be at the start of the list

        small_price_list = []

        for price in prices_list:

            small_price_list.append(price)

            if len(small_price_list) >= self.slow_length:
                break

        fast_list = self.make_ema_list(self.fast_EMA, small_price_list, self.fast_length)
        slow_list = self.make_ema_list(self.slow_EMA, small_price_list, self.slow_length)

        difference_list = self.find_difference(fast_list, slow_list)

        """
        Value = MovingAverage(averageType, close, fastLength) - MovingAverage(averageType, close, slowLength);
        Avg = MovingAverage(averageType, Value, MACDLength);

        Diff = Value - Avg;
        ZeroLine = 0;

        UpSignal = if Diff crosses above ZeroLine then ZeroLine else Double.NaN;
        DownSignal = if Diff crosses below ZeroLine then ZeroLine else Double.NaN;
        """

        return difference_list
