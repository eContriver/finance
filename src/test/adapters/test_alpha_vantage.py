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
from datetime import timedelta, datetime
from typing import Dict, List
from unittest import TestCase

from main.adapters.alpha_vantage import AlphaVantage, get_adjusted_ratio
from main.application.adapter import request_limit_with_timedelta_delay, DataType
from main.application.time_interval import TimeInterval
from main.application.argument import Argument, ArgumentKey
from main.application.value_type import ValueType


class MockAlphaVantage(AlphaVantage):  # -> List(str), str
    def get_url_response(self, url: str, query, cache: bool = True, data_type: DataType = DataType.JSON,
                         delay: bool = True):
        data = []
         # with tempfile.TemporaryDirectory() as tmpdirname:
        data_file = '/test/file'
        if query['function'] == 'LISTING_STATUS':
            data.append(['title'])
            data.append(['testvalue'])
        elif query['function'] == 'TIME_SERIES_INTRADAY':
            data.append(['title'])
            data.append(['testvalue'])
        return data, data_file


class TestAlphaVantage(TestCase):
    def test_delay_requests(self):
        # testing_utils.configure_test_logging()
        start_time = datetime.now()
        historic_requests = {
            '/path1': start_time,
            '/path2': start_time,
            '/path3': start_time,
            '/path4': start_time,
            '/path5': start_time,
        }
        max_timeframe = timedelta(milliseconds=500)
        request_limit_with_timedelta_delay(buffer=0.0, historic_requests=historic_requests,
                                           max_timeframe=max_timeframe, max_requests=5)
        request_limit_with_timedelta_delay(buffer=0.0, historic_requests=historic_requests,
                                           max_timeframe=max_timeframe, max_requests=5)
        end_time = datetime.now()
        delta_time = end_time - start_time
        self.assertLessEqual(max_timeframe, delta_time)

    def test_get_adjusted_ratio(self):
        time_data: Dict[str, str] = {
            '5. adjusted close': '10.0',
            '4. close': '5.0',
        }
        self.assertEqual(get_adjusted_ratio(time_data), 2.0)

    # def test_find_symbol_in_data(self):
    #     symbol: str = 'TEST'
    #     adapter: AlphaVantage = AlphaVantage(symbol)
    #     find_symbol_in_data(symbol)
    #     self.fail()

    def test_get_equities_list(self):
        adapter: AlphaVantage = MockAlphaVantage('TEST')
        equities: List[str] = adapter.get_equities_list()
        self.assertEqual(equities[0], 'testvalue')

    # def test_get_prices_response(self):
    #     adapter: AlphaVantage = MockAlphaVantage('TEST')
    #     adapter.add_argument(Argument(ArgumentKey.INTERVAL, TimeInterval.HOUR))
    #     adapter.get_prices_response(ValueType.CLOSE)
    #     start_time = datetime.now()
    #     self.assertEqual(adapter.get_value(start_time, ValueType.CLOSE), 1.0)

    # def test_get_stock_prices_response(self):
    #     self.fail()
    #
    # def test_get_digital_currency_response(self):
    #     self.fail()
    #
    # def test_translate(self):
    #     self.fail()
    #
    # def test_get_macd_response(self):
    #     self.fail()
    #
    # def test_get_sma_response(self):
    #     self.fail()
    #
    # def test_get_rsi_response(self):
    #     self.fail()
    #
    # def test_get_earnings_response(self):
    #     self.fail()
    #
    # def test_translate_earnings(self):
    #     self.fail()
    #
    # def test_get_income_response(self):
    #     self.fail()
    #
    # def test_translate_income(self):
    #     self.fail()
    #
    # def test_get_balance_sheet_response(self):
    #     self.fail()
    #
    # def test_translate_balance_sheet(self):
    #     self.fail()
    #
    # def test_get_cash_flow_response(self):
    #     self.fail()
    #
    # def test_translate_cash_flow(self):
    #     self.fail()
    #
    # def test_validate_json_response(self):
    #     self.fail()
    #
    # def test_get_indicator_key(self):
    #     self.fail()
    #
    # def test_get_is_digital_currency(self):
    #     self.fail()
    #
    # def test_get_is_listed(self):
    #     self.fail()
    #
    # def test_get_is_physical_currency(self):
    #     self.fail()
