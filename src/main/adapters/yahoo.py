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

import os.path
from datetime import datetime, timedelta
from typing import Dict, Optional, List

import pandas
import pandas_datareader
import robin_stocks as rs
from pandas_datareader import DataReader

from main.application.adapter import AssetType, DataType, Adapter, get_response_value_or_none, \
    IntervalNotSupportedException
from main.application.argument import ArgumentKey
from main.application.converter import Converter
from main.application.time_interval import TimeInterval
from main.application.value_type import ValueType
from main.common.time_zones import TimeZones


class Yahoo(Adapter):
    # span: timedelta
    name: str = 'yahoo'

    def __init__(self, symbol: str, asset_type: Optional[AssetType] = None):
        super().__init__(symbol, asset_type)
        script_dir = os.path.dirname(os.path.realpath(__file__))
        self.cache_dir = os.path.join(script_dir, '..', '..', '..', '.cache', Yahoo.name)
        # self.span = '5year'
        # 'hour', 'day', 'week', 'month', '3month', 'year', '5year'
        years = 10
        # self.span = timedelta(weeks=52*years)
        self.converters: List[Converter] = [
            # we allow for multiple strings to be converted into the value type, first match is used
            Converter(ValueType.OPEN, self.get_prices_response, ['1. open', '1a. open (USD)'], adjust_values=True),
            Converter(ValueType.HIGH, self.get_prices_response, ['2. high', '2a. high (USD)'], adjust_values=True),
            Converter(ValueType.LOW, self.get_prices_response, ['3. low', '3a. low (USD)'], adjust_values=True),
            Converter(ValueType.CLOSE, self.get_prices_response, ['4. close', '4a. close (USD)'],
                      adjust_values=True),
            Converter(ValueType.VOLUME, self.get_prices_response, ['5. volume']),
            # Converter(ValueType.RSI, self.get_rsi_response, ['RSI']),
            # Converter(ValueType.MACD, self.get_macd_response, ['MACD']),
            # Converter(ValueType.MACD_HIST, self.get_macd_response, ['MACD_Hist']),
            # Converter(ValueType.MACD_SIGNAL, self.get_macd_response, ['MACD_Signal']),
            # Converter(ValueType.SMA, self.get_sma_response, ['SMA']),
            # Converter(ValueType.EPS, self.get_earnings_response, ['reportedEPS']),
            # Converter(ValueType.REVENUE, self.get_income_response, ['totalRevenue']),
            # ESTIMATED_EPS = auto()
            # SURPRISE_EPS = auto()
            # SURPRISE_PERCENTAGE_EPS = auto()
            # GROSS_PROFIT = auto()
            # TOTAL_REVENUE = auto()
            # OPERATING_CASH_FLOW = auto()
            # Converter(ValueType.DEPRECIATION, self.get_cash_flow_response, ['depreciationDepletionAndAmortization']),
            # Converter(ValueType.RECEIVABLES, self.get_cash_flow_response, ['changeInReceivables']),
            # Converter(ValueType.INVENTORY, self.get_cash_flow_response, ['changeInInventory']),
            # Converter(ValueType.PAYABLES, self.get_cash_flow_response, ['operatingCashflow']),
            # Converter(ValueType.CAPITAL_EXPENDITURES, self.get_cash_flow_response, ['capitalExpenditures']),
            # Converter(ValueType.FREE_CASH_FLOW, self.get_cash_flow_response, ['operatingCashflow']),

            # Converter(ValueType.CASH_FLOW, self.get_cash_flow_response, ['operatingCashflow']),
            # Converter(ValueType.DIVIDENDS, self.get_cash_flow_response, ['dividendPayout']),
            # Converter(ValueType.NET_INCOME, self.get_cash_flow_response, ['netIncome']),
            # Converter(ValueType.ASSETS, self.get_balance_sheet_response, ['totalAssets']),
            # Converter(ValueType.LIABILITIES, self.get_balance_sheet_response, ['totalLiabilities']),
            # Converter(ValueType.SHORT_DEBT, self.get_balance_sheet_response, ['shortTermDebt']),
            # Converter(ValueType.LONG_DEBT, self.get_balance_sheet_response, ['longTermDebt']),
            # This value was very wrong for BRK-A, it says something like 3687360528 shares outstanding, while there
            # are actually only something like 640000
            # Converter(ValueType.SHARES, self.get_balance_sheet_response, ['commonStockSharesOutstanding']),
            # This is not quite right...
            # https://www.fool.com/investing/stock-market/basics/earnings-per-share/

            # Let's walk through an example EPS calculation using Netflix (NASDAQ:NFLX). For its most recent fiscal
            # year, the company reported a net income of $2,761,395,000 and total shares outstanding of 440,922,
            # 000. The company's balance sheet indicates Netflix has not issued any preferred stock, so we don't need
            # to subtract out preferred dividends. Dividing $2,761,395,000 into 440,922,000 produces an EPS value of
            # $6.26. (this is what we get, and even then the number of outstanding shares differs slightly)
            #
            # Let's calculate the diluted EPS for Netflix. The company has granted 13,286,000 stock options to
            # employees, which raises the total outstanding share count to 454,208,000. Dividing the same $2,761,395,
            # 000 of net income into 454,208,000 equals an EPS value of $6.08.
            # Converter(ValueType.DILUTED_SHARES, self.get_balance_sheet_response, ['commonStockSharesOutstanding']),
            # Converter(ValueType.EQUITY, self.get_balance_sheet_response, ['totalShareholderEquity']),
        ]

    def get_prices_response(self, value_type: ValueType) -> None:
        if self.asset_type is AssetType.DIGITAL_CURRENCY:
            self.get_digital_currency_response(value_type)
        else:
            self.get_stock_prices_response(value_type)

    def get_stock_prices_response(self, value_type: ValueType) -> None:
        interval: TimeInterval = self.get_argument_value(ArgumentKey.INTERVAL)
        end_time: Optional[datetime] = self.get_argument_value(ArgumentKey.END_TIME)
        end_time = datetime.now() if end_time is None else end_time
        start_time: Optional[datetime] = self.get_argument_value(ArgumentKey.START_TIME)
        start_time = end_time - timedelta(days=1) if start_time is None else start_time
        query = {
            'name':        self.symbol,
            'data_source': Yahoo.name,
            'start':       start_time,
            'end':         end_time
        }
        record_count = (end_time - start_time) / interval.timedelta
        output_size = "compact" if record_count < 100 else "full"
        if interval == TimeInterval.HOUR:
            query["function"] = "TIME_SERIES_INTRADAY"
            query["interval"] = '60min'
            query["adjusted"] = True
            query["outputsize"] = output_size
            key = 'Time Series (60min)'
        elif interval == TimeInterval.DAY:
            query["function"] = "TIME_SERIES_DAILY_ADJUSTED"
            query["outputsize"] = output_size
            key = 'Time Series (Daily)'
        elif interval == TimeInterval.WEEK:
            query["function"] = "TIME_SERIES_WEEKLY_ADJUSTED"
            key = 'Weekly Adjusted Time Series'
        elif interval == TimeInterval.MONTH:
            query["function"] = "TIME_SERIES_MONTHLY_ADJUSTED"
            key = 'Monthly Adjusted Time Series'
        else:
            raise IntervalNotSupportedException(f"Specified interval is not supported: '{interval}' "
                                                f"(for: {self.__class__.__name__})")
        raw_response, data_file = self.get_url_response(self.url, query)
        self.validate_json_response(data_file, raw_response)
        self.translate(raw_response, value_type, key)

    @staticmethod
    def find_symbol_in_data(data, entry):
        contains = False
        for row in data:
            if row[0] == entry:
                contains = True
                break
        return contains

    def delay_requests(self, data_file: str) -> None:
        pass

    def get_is_stock(self) -> bool:
        today: datetime = datetime.now(TimeZones.get_tz())
        # yesterday = today - timedelta(days=1)
        args = {
            'name':        self.symbol,
            'data_source': Yahoo.name,
            'start':       today.strftime('%Y-%m-%d'),
            'end':         today.strftime('%Y-%m-%d')
        }
        found_listed = False
        try:
            raw_response, data_file = self.get_api_response(DataReader, args, cache=True, data_type=DataType.DATA_FRAME)
            found_listed = raw_response.shape[0] >= 1
        except (pandas_datareader._utils.RemoteDataError):
            pass  # this means that the symbol was not found
        return found_listed

    def get_is_digital_currency(self) -> bool:
        return False

    def get_is_physical_currency(self) -> bool:
        return 'USD' == self.base_symbol

    def get_stock_series_response(self):
        today: datetime = datetime.now(TimeZones.get_tz())
        today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        # yesterday = today - timedelta(days=1)
        args = {
            'name':        self.symbol,
            'data_source': Yahoo.name,
            'start':       today - self.span,
            'end':         today
        }
        raw_response, data_file = self.get_api_response(DataReader, args, cache=True, data_type=DataType.DATA_FRAME)
        data = self.translate_series(raw_response)
        return data

    def translate_interval(self):
        if self.series_interval == TimeInterval.DAY:
            interval = 'day'
        else:
            raise RuntimeError('Unknown interval: {}'.format(self.series_interval))
        return interval

    def translate_series(self, response_data, data_date_format='%Y-%m-%dT%H:%M:%SZ') -> Dict[
        datetime, Dict[ValueType, float]]:
        translated = {}
        assert not response_data.empty, "The response data was empty"
        to_translate = response_data.copy()
        to_translate.index = pandas.to_datetime(to_translate.index)
        # translated = translated.apply(self.)
        to_translate = response_data.to_dict(orient='index')
        for instance, values in to_translate.items():
            translated[instance] = {}
            for value_type in ValueType:
                value = get_response_value_or_none(values, value_type)
                if value is not None:
                    ratio = self.get_adjusted_ratio(values)
                    value = value * ratio
                    translated[instance][value_type] = value
        return translated

    def get_digital_series_response(self):
        args = {
            "symbol":   self.symbol,
            "span":     self.span,  # self.end_at...
            "interval": self.translate_interval(),
        }
        raw_response, data_file = self.get_api_response(rs.yahoo.get_crypto_historicals, args)
        assert raw_response, "The response data was empty"
        data = self.translate_series(raw_response)
        return data

    def get_indicator_key(self):
        self.calculate_asset_type()
        indicator_key = self.symbol
        if self.asset_type == AssetType.DIGITAL_CURRENCY:
            indicator_key = "{}-{}".format(self.symbol, self.base_symbol)  # e.g. BTC-USD
        return indicator_key

    def get_holdings(self):
        data = self.get_stock_positions()
        data = merge(data, self.get_crypto_positions())
        data = merge(data, self.get_account_info())
        return data

    def get_historic_value(self) -> Dict[datetime, float]:
        args = {
            'span':     'month',
            'interval': 'day',
            # 'bounds': 'extended',
        }
        raw_response, data_file = self.get_api_response(rs.yahoo.get_historical_portfolio, args, cache=False)
        assert raw_response, "The response data was empty"
        if len(raw_response) == 1:
            assert raw_response[0] is not None, "The response data was empty"
        data: Dict[datetime, float] = self.translate_portfolio(raw_response['equity_historicals'])
        return data

    @staticmethod
    def translate_portfolio(response_data, data_date_format='%Y-%m-%dT%H:%M:%SZ') -> Dict[datetime, float]:
        translated: Dict[datetime, float] = {}
        assert response_data, "The response data was empty"
        for item in response_data:
            assert item is not None, "Received a None item while translating response data"
            dt = datetime.strptime(item['begins_at'], data_date_format)
            translated[dt] = float(item['adjusted_close_equity'])
        return translated

    def get_account_info(self):
        args = {
        }
        raw_response, data_file = self.get_api_response(rs.yahoo.load_phoenix_account, args, cache=False)
        assert raw_response, "The response data was empty"
        data = {
            raw_response['account_buying_power']['currency_code']: float(
                raw_response['account_buying_power']['amount'])
        }
        return data

    # def get_stock_positions(self):
    #     args = {
    #     }
    #     raw_response, data_file = self.get_api_response(rs.yahoo.build_holdings, args, cache=False)
    #     assert raw_response, "The response data was empty"
    #     data = {}
    #     for symbol, item in raw_response.items():
    #         data[symbol] = float(item['quantity'])
    #     return data

    def get_crypto_positions(self):
        args = {
        }
        raw_response, data_file = self.get_api_response(rs.yahoo.get_crypto_positions, args, cache=False)
        assert raw_response, "The response data was empty"
        data = {}
        for item in raw_response:
            data[item['currency']['code']] = float(item['quantity'])
        return data

    def get_open_orders(self):
        orders = self.get_open_stock_orders()
        orders += self.get_open_crypto_orders()
        return orders

    # def get_open_stock_orders(self):
    #     args = {
    #     }
    #     raw_response, data_file = self.get_api_response(rs.yahoo.get_all_open_stock_orders, args, cache=False)
    #     orders = []
    #     for item in raw_response:
    #         side = OrderSide.BUY if item['side'] == 'buy' else OrderSide.SELL
    #         data_date_format = '%Y-%m-%dT%H:%M:%S.%f%z'
    #         dt = datetime.strptime(item['created_at'], data_date_format)
    #
    #         args = {
    #             'url': item['instrument']
    #         }
    #         instrument_response, instrument_file = self.get_api_response(rs.yahoo.get_instrument_by_url, args)
    #
    #         if item['type'] == 'limit':
    #             orders.append(LimitOrder(instrument_response['symbol'], side, float(item['price']), float(item['quantity']), dt))
    #         elif item['type'] == 'stop':
    #             orders.append(StopOrder(instrument_response['symbol'], side, float(item['price']), float(item['quantity']), dt))
    #         else:
    #             raise RuntimeError("Unsupported order type: {}".format(item['type']))
    #     return orders
    #     # orders = self.translate_orders(raw_response, rs.yahoo.get_stock_order_info)
    #     # return orders

    # def get_open_crypto_orders(self):
    #     args = {
    #     }
    #     raw_response, data_file = self.get_api_response(rs.yahoo.get_all_open_crypto_orders, args, cache=False)
    #     orders = []
    #     for item in raw_response:
    #         side = OrderSide.BUY if item['side'] == 'buy' else OrderSide.SELL
    #         data_date_format = '%Y-%m-%dT%H:%M:%S.%f%z'
    #         dt = datetime.strptime(item['created_at'], data_date_format)
    #
    #         args = {
    #         }
    #         pair_response, pair_file = self.get_api_response(rs.yahoo.get_currency_pairs, args)
    #
    #         symbol = None
    #         for pair_item in pair_response:
    #             if pair_item['id'] == item['currency_pair_id']:
    #                 symbol = pair_item['asset_currency']['code']
    #
    #         if item['type'] == 'limit':
    #             orders.append(LimitOrder(symbol, side, float(item['price']), float(item['quantity']), dt))
    #         elif item['type'] == 'stop':
    #             orders.append(StopOrder(symbol, side, float(item['price']), float(item['quantity']), dt))
    #         else:
    #             raise RuntimeError("Unsupported order type: {}".format(item['type']))
    #     return orders
    #     # orders = self.translate_orders(raw_response, rs.yahoo.get_crypto_order_info)
    #     # return orders

    # def translate_orders(self, raw_response, info_api):
    #     orders = []
    #     for item in raw_response:
    #         side = OrderSide.BUY if item['side'] == 'buy' else OrderSide.SELL
    #         data_date_format = '%Y-%m-%dT%H:%M:%S.%f%z'
    #         dt = datetime.strptime(item['created_at'], data_date_format)
    #         order_id = item['id']
    #         order_info = self.get_order_info(info_api, order_id)
    #         if item['type'] == 'limit':
    #             orders.append(LimitOrder(order_info['symbol'], side, float(item['price']), float(item['quantity']), dt))
    #         elif item['type'] == 'stop':
    #             orders.append(LimitOrder(order_info['symbol'], side, float(item['price']), float(item['quantity']), dt))
    #         else:
    #             raise RuntimeError("Unsupported order type: {}".format(item['type']))
    #     return orders
    #
    # def get_order_info(self, info_api, order_id):
    #     if info_api == rs.yahoo.get_stock_order_info:
    #         args = {'orderID': order_id}
    #     else:
    #         args = {'order_id': order_id}
    #     raw_response, data_file = self.get_api_response(info_api, args, cache=False)
    #     return raw_response
