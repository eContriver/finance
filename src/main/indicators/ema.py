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

from main.application.indicator import Indicator


class EMA(Indicator):
    """
    Exponential Moving Average
    """

    # when you start, declare the length of the EMA you want to be using
    def __init__(self, length):
        self.averaging_length = length
        self.SMOOTHING_COEFFICIENT = 2 / (self.averaging_length + 1)

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

        ema_position = 1
        ema_total = prices_list[0]

        while ema_position < self.averaging_length:

            if ema_position > len(prices_list):
                break
            price = prices_list[ema_position]
            ema_total = self.SMOOTHING_COEFFICIENT * price + (1 - self.SMOOTHING_COEFFICIENT) * ema_total

            ema_position += 1
        '''
        `EMA1 = price1;`
        `EMA2 = α*price2 + (1 - α)*EMA1;`
        `EMA3 = α*price3 + (1 - α)*EMA2;`
        `EMAN = α*priceN + (1 - α)*EMAN-1;`

        where α is a smoothing coefficient equal to `2/(length + 1)`.
        '''

        # price 1 is the [0] in the small_price_list
        return ema_total
