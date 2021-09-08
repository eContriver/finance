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


import logging
import sys
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Dict, Optional, List

import matplotlib.pyplot as plt
import pandas
from pytrends.request import TrendReq

from main.application.adapter import insert_column, AssetType, Adapter, TimeInterval
from main.application.adapter_collection import AdapterCollection, set_all_cache_key_dates
from main.application.argument import Argument, ArgumentType
from main.application.value_type import ValueType
from main.common.locations import Locations
from main.common.report import Report
from main.application.runner import Runner, get_asset_type_overrides, get_adapter_class


class TrendReportType(Enum):
    INTEREST_OVER_TIME = auto()
    HISTORICAL_INTEREST = auto()
    REGION = auto()
    TRENDING = auto()
    TOP_CHARTS = auto()
    KEYWORD_SUGGESTION = auto()
    RELATED_QUERY = auto()
    RELATED_TOPIC = auto()


class TrendRunner(Runner):
    terms: List[str]
    symbol: Optional[str]
    adapter_class: Optional[type]
    base_symbol: str
    price_interval: TimeInterval
    asset_type_overrides: Dict[str, AssetType]
    report_types: List[TrendReportType]

    def __init__(self):
        super().__init__()
        self.terms = []
        self.symbol = None
        self.adapter_class = None
        self.base_symbol = 'USD'
        self.price_interval = TimeInterval.DAY
        self.asset_type_overrides = {}
        self.report_types = []

    def start(self, locations: Locations) -> bool:
        logging.info("#### Starting trend runner...")
        success = True

        # means to auto select based off self.symbol
        collection: AdapterCollection = self.get_collection()

        pytrend = TrendReq()
        pytrend.build_payload(kw_list=self.terms)

        if TrendReportType.INTEREST_OVER_TIME in self.report_types:
            time_data = pytrend.interest_over_time()
            close_column: pandas.Series = collection.get_column(self.symbol, ValueType.CLOSE)
            max_price = close_column.max()
            insert_column(time_data, ValueType.CLOSE, close_column.index.tolist(),
                          ((close_column.values / max_price) * 100.0).tolist())
            time_data.interpolate(method='time', inplace=True)
            logging.info(f"Interest over time:\n{time_data}")
            time_data.rename(columns={ValueType.CLOSE: f"Closing Price {self.symbol}"}, inplace=True)
            time_data.drop(columns='isPartial').plot()

        # Chart by hour - TODO: Ensure we are actually getting the data before the price changes, add caching
        if TrendReportType.HISTORICAL_INTEREST in self.report_types:
            pytrend.get_historical_interest(self.terms, year_start=2018, month_start=1, day_start=1, hour_start=0,
                                            year_end=2018, month_end=2, day_end=1, hour_end=0, cat=0, geo='', gprop='',
                                            sleep=0)

        if TrendReportType.REGION in self.report_types:
            region_data = pytrend.interest_by_region()
            logging.info(f"Interest by region:\n{region_data.head(10)}")
            region_data.reset_index().plot(x='geoName', y=self.terms[0], figsize=(120, 10), kind='bar')

        if TrendReportType.TRENDING in self.report_types:
            trending_data = pytrend.trending_searches(pn='united_states', )
            logging.info(f"Trending real-time interest:\n{trending_data.to_string()}")

        if TrendReportType.TOP_CHARTS in self.report_types:
            top_data = pytrend.top_charts(2019, hl='en-US', tz=300, geo='GLOBAL')
            logging.info(f"Top charts:\n{top_data.to_string()}")

        if TrendReportType.KEYWORD_SUGGESTION in self.report_types:
            keywords = pytrend.suggestions(keyword=self.terms[0])
            suggested_data = pandas.DataFrame(keywords)
            logging.info(f"Keyword suggestions:\n{suggested_data.to_string()}")

        if TrendReportType.RELATED_QUERY in self.report_types:
            related_queries = pytrend.related_queries()
            for term in self.terms:
                logging.info(f"Related queries, top for '{term}':\n{related_queries[term]['top']}")
                logging.info(f"Related queries, rising for '{term}':\n{related_queries[term]['rising']}")

        if TrendReportType.RELATED_TOPIC in self.report_types:
            related_topic = pytrend.related_topics()
            for term in self.terms:
                logging.info(f"Related topics, top:\n{related_topic[term]['top']}")
                logging.info(f"Related topics, rising:\n{related_topic[term]['rising']}")

        plt.show(block=True)

        return success

    def get_collection(self) -> AdapterCollection:
        asset_type: Optional[AssetType] = self.asset_type_overrides[self.symbol] if self.symbol in \
                                                                                    self.asset_type_overrides else None
        adapter: Adapter = self.adapter_class(self.symbol, asset_type)
        end_time = datetime.now()
        adapter.asset_type = asset_type
        adapter.add_argument(Argument(ArgumentType.START_TIME, end_time - timedelta(weeks=52)))
        adapter.add_argument(Argument(ArgumentType.END_TIME, end_time))
        adapter.add_argument(Argument(ArgumentType.INTERVAL, self.price_interval))
        adapter.request_value_types = [ValueType.CLOSE]
        collection: AdapterCollection = AdapterCollection()
        collection.add(adapter)
        set_all_cache_key_dates(collection.adapters, datetime.now())
        collection.retrieve_all_data()
        return collection

    def get_config(self) -> Dict:
        asset_type_overrides = {}
        for symbol, asset_type in self.asset_type_overrides.items():
            asset_type_overrides[symbol] = asset_type.name
        config = {
            'adapter_class': self.adapter_class.__name__,
            'base_symbol': self.base_symbol,
            'terms': self.terms,
            'symbol': self.symbol,
            'price_interval': self.price_interval.value,
            'asset_type_overrides': asset_type_overrides,
        }
        return config

    def set_from_config(self, config, config_path):
        report_types: List[str] = config['report_types']
        self.report_types = [TrendReportType[report_type] for report_type in report_types]
        self.asset_type_overrides = get_asset_type_overrides(config['asset_type_overrides'])
        self.terms = config['terms']
        self.symbol = config['symbol']
        self.adapter_class = get_adapter_class(config['adapter_class'])
        self.base_symbol = config['base_symbol']
        # self.price_interval = TimeInterval(config['price_interval'])
        self.check_member_variables(config_path)

    def check_member_variables(self, config_path: str):
        # validate_type('symbol', self.symbol, dict, config_path)
        # if not self.symbol:
        #     raise NoSymbolsSpecifiedException(f"Please specify at least one symbol under 'symbol' in: "
        #                                       f"{config_path}")
        pass

    def get_run_name(self):
        return "Google"
        # return f"{self.price_interval.value.title()}_{self.adapter_class.__name__}"

    @staticmethod
    def get_final_close(collection: AdapterCollection, symbol):
        end_time: datetime = collection.get_end_time(symbol, ValueType.CLOSE)
        # data: Dict[datetime, float] = symbol_adapter.get_column(symbol, ValueType.ADJUSTED_CLOSE)
        price: float = collection.get_value(symbol, end_time, ValueType.CLOSE)
        return price
