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

import inspect
from datetime import datetime, timedelta
from typing import Optional

from main.adapters.adapter import Adapter


class Order(Adapter):

    def __init__(self, symbol: str):
        super(Order, self).__init__(symbol)

    def place_buy_limit_order(self, quantity: float, price: float):
        raise RuntimeError("Implement: {}".format(inspect.currentframe().f_code.co_name))

    def place_buy_stop_order(self, quantity: float, price: float):
        raise RuntimeError("Implement: {}".format(inspect.currentframe().f_code.co_name))

    def place_buy_market_order(self, quantity: float):
        raise RuntimeError("Implement: {}".format(inspect.currentframe().f_code.co_name))

    def place_sell_limit_order(self, quantity: float, price: float):
        raise RuntimeError("Implement: {}".format(inspect.currentframe().f_code.co_name))

    def place_sell_stop_order(self, quantity: float, price: float):
        raise RuntimeError("Implement: {}".format(inspect.currentframe().f_code.co_name))

    def place_sell_market_order(self, quantity: float):
        raise RuntimeError("Implement: {}".format(inspect.currentframe().f_code.co_name))

    def get_holdings(self):
        raise RuntimeError("Implement: {}".format(inspect.currentframe().f_code.co_name))

    def get_historic_value(self):
        raise RuntimeError("Implement: {}".format(inspect.currentframe().f_code.co_name))

    def get_open_orders(self):
        raise RuntimeError("Implement: {}".format(inspect.currentframe().f_code.co_name))
