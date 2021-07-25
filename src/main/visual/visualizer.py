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


from datetime import datetime, timedelta
import math
from typing import Optional, Dict, List, Any

import matplotlib.pyplot as plt
import pandas
from matplotlib import dates
from mplfinance.original_flavor import candlestick_ochl

from main.adapters.adapter import Adapter, get_start_time
from main.adapters.value_type import ValueType
from main.adapters.adapter_collection import AdapterCollection
from main.portfolio.portfolio import Portfolio
from main.portfolio.order import OrderSide, Order
from main.visual.annotation import Annotation
from main.visual.extra import Extra


class PricePlot:
    def __init__(self, data: pandas.DataFrame, color, label: Optional[str] = None,
                 share_y_axis: bool = False):
        self.color = color
        self.data = data
        self.name = 'Name'
        self.label = self.name if label is None else label
        self.labelColor = 'black'
        self.share_y_axis = share_y_axis
        self.annotations: List[Annotation] = []  # HasAnnotations decorator?


class Visualizer:
    title: str
    collection: AdapterCollection
    portfolios: List[Portfolio]
    extras: List[Extra]
    price_plots: Dict[str, PricePlot]
    annotations: List[Annotation]
    color_index: int
    annotate_opened_orders: bool
    annotate_canceled_orders: bool
    annotate_closed_orders: bool
    annotate_close_prices: bool
    annotate_open_prices: bool
    draw_high_prices: bool
    draw_low_prices: bool
    draw_close_prices: bool
    draw_open_prices: bool

    def __init__(self, title: str, collection: AdapterCollection, portfolios: List[Portfolio] = []):
        self.title = title
        self.collection = collection
        self.portfolios = portfolios
        self.extras = []
        self.price_plots = {}
        self.annotations = []
        self.color_index = 0
        self.annotate_opened_orders = False
        self.annotate_canceled_orders = False
        self.annotate_closed_orders = True
        self.annotate_close_prices = False
        self.annotate_open_prices = False
        self.draw_high_prices = True
        self.draw_low_prices = True
        self.draw_close_prices = True
        self.draw_open_prices = True

    def plot_all(self, block: bool = True):
        portfolio_count = len(self.portfolios)
        if portfolio_count == 0:
            self.plot_collection(block)
        elif portfolio_count == 1:
            portfolio = self.portfolios[0]
            self.plot_portfolio_candle(portfolio, block)
            # self.plot_portfolio(block)
        else:
            self.plot_portfolios(block)

    def plot_collection(self, block: bool = True):
        for adapter in self.collection.adapters:
            self.add_series_data(adapter, portfolio=None)
        row_titles = []
        for adapter in self.collection.adapters:
            assert adapter.symbol in self.price_plots, 'The symbol {} has no data'.format(adapter.symbol)
            row_titles.append(self.price_plots[adapter.symbol].label)
            for value_type in adapter.request_value_types:
                value_type_filter = [
                    ValueType.HIGH,
                    ValueType.OPEN,
                    ValueType.CLOSE,
                    ValueType.LOW,
                    ValueType.RSI,
                    ValueType.MACD,
                    ValueType.MACD_HIST,
                    ValueType.MACD_SIGNAL,
                ]
                if value_type in value_type_filter:
                    continue
                adapter.add_extra_data(value_type, self)
        columns = 1  # 1 (valueData) + self.extras
        extra: Extra
        for extra in self.extras:
            if extra.label not in row_titles:
                row_titles.append(extra.label)
        rows = len(row_titles)
        fig, ax = plt.subplots(rows, columns, sharex='all', gridspec_kw={'hspace': 0})
        fig.suptitle(self.title)
        fig.patch.set_facecolor((0.6, 0.6, 0.6))
        bg_color = (0.5, 0.5, 0.5)
        plotted_labels = {}
        plots = {}

        row = self.add_or_get_row('Price per Unit', plotted_labels)
        this_ax = ax if rows == 1 else ax[row]
        this_ax.set_facecolor(bg_color)
        for adapter in self.collection.adapters:
            self.candle_sub_plot(this_ax, self.price_plots[adapter.symbol], self.annotations)

        for extra in self.extras:
            row = self.add_or_get_row(extra.label, plotted_labels)
            this_ax = ax if rows == 1 else ax[row]
            this_ax.set_facecolor(bg_color)
            if row not in plots:
                plots[row] = []
            if extra.as_candlesticks:
                pass # Can we (or do we want to) move the series to be an extra as is added by the series already
                # self.series_sub_plot(this_ax, self.series, self.annotations)
            else:
                plots[row] += self.sub_plot(this_ax, extra.name, extra.label, extra.data, extra.color, self.annotations)
        for row in plots.keys():
            labels = [plot.get_label() for plot in plots[row]]
            this_ax = ax if rows == 1 else ax[row]
            legend = this_ax.legend(plots[row], labels, loc=0)
            legend.get_frame().set_facecolor((0.6, 0.6, 0.6))
        fig.subplots_adjust(top=0.95, bottom=0.05, right=0.95, left=0.05)
        mng = plt.get_current_fig_manager()
        mng.full_screen_toggle()
        plt.show(block=block)

    COLOR_WHEEL: List[str] = [
        '#f70', '#70f',  # branding colors and the following is similar to green: '#7f0',

        '#000',

        # '#f00', '#0f0', '#00f',  # used in indicators
        '#ff0', '#f0f', '#0ff',

        '#f07', '#0f7', '#07f',  # fluorescent

        '#f77', '#7f7', '#77f',
        '#ff7', '#f7f', '#7ff',

        '#faa', '#afa', '#aaf',
        '#ffa', '#faf', '#aff',

        '#700', '#070', '#007',
        '#770', '#707', '#077',

        # '#a00', '#0a0', '#00a',  # used in indicators
        '#aa0', '#a0a', '#0aa',
    ]

    def get_next_color(self) -> str:
        color = self.COLOR_WHEEL[self.color_index]
        if self.color_index >= (len(self.COLOR_WHEEL) - 1):
            self.color_index = 0
        else:
            self.color_index += 1
        return color

    def plot_portfolio(self, block: bool = True):
        portfolio = self.portfolios[0]
        # Extras
        for symbol, adapter in self.collection.symbol_handles.items():
            self.add_series_data(adapter, portfolio, symbol)
        for key, data in portfolio.indicator_data.items():
            data = portfolio.filter_dict_times(data)
            self.extras.append(Extra(key, data, self.get_next_color(), 'Custom Indicator'))
        # Annotations
        for order in portfolio.closed_orders:
            self.annotate_closed_order(order)
        for order in portfolio.canceled_orders:
            self.annotate_canceled_order(order)
        for order in portfolio.opened_orders:
            self.annotate_opened_order(order)
        columns = 1  # 1 (valueData) + self.extras
        row_titles = []
        extra: Extra
        for extra in self.extras:
            if extra.label not in row_titles:
                row_titles.append(extra.label)
        rows = 1 + len(row_titles)
        fig, ax = plt.subplots(rows, columns, sharex='all', gridspec_kw={'hspace': 0})
        fig.suptitle(self.title)
        fig.patch.set_facecolor((0.6, 0.6, 0.6))
        bg_color = (0.5, 0.5, 0.5)
        row = 0
        ax[row].set_facecolor(bg_color)
        plots = {row: []}
        plots[row] += self.sub_plot(ax[0], "Portfolio Value", "Value", portfolio.data, self.get_next_color(), []) # '#f00', [])
        row += 1
        plotted_labels = {}
        for extra in self.extras:
            this_row = self.add_or_get_row(extra.label, plotted_labels, row)
            ax[this_row].set_facecolor(bg_color)
            # ax[this_row].set_title(extra.label)
            if this_row not in plots:
                plots[this_row] = []
            annotations = self.annotations
            adjust_annotations = True
            if adjust_annotations:
                for annotation in annotations:
                    annotation.y = extra.data.loc[annotation.x, :][0]
            plots[this_row] += self.sub_plot(ax[this_row], extra.name, extra.label, extra.data, extra.color, annotations)
        for row in plots.keys():
            labels = [plot.get_label() for plot in plots[row]]
            legend = ax[row].legend(plots[row], labels, loc=0)
            legend.get_frame().set_facecolor((0.6, 0.6, 0.6))
        fig.subplots_adjust(top=0.95, bottom=0.05, right=0.95, left=0.05)
        mng = plt.get_current_fig_manager()
        mng.full_screen_toggle()
        plt.show(block=block)

    def plot_portfolio_candle(self, portfolio: Portfolio, block: bool = True):
        row_titles: List[str] = []
        for adapter in self.collection.adapters:
            self.add_series_data(adapter, portfolio)
            title = "{} {}".format(adapter.symbol, self.price_plots[adapter.symbol].label)
            if title not in row_titles:
                row_titles.append(title)
        for key, data in portfolio.indicator_data.items():
            data = portfolio.filter_dict_times(data)
            self.extras.append(Extra(key, data, self.get_next_color(), 'Custom Indicator'))
        # Annotations
        for order in portfolio.closed_orders:
            self.annotate_closed_order(order)
        for order in portfolio.canceled_orders:
            self.annotate_canceled_order(order)
        for order in portfolio.opened_orders:
            self.annotate_opened_order(order)
        # Extras
        columns = 1  # 1 (valueData) + self.extras
        for extra in self.extras:
            if extra.label not in row_titles:
                row_titles.append(extra.label)
        rows = 1 + len(row_titles)
        fig, ax = plt.subplots(rows, columns, sharex='all', gridspec_kw={'hspace': 0})
        fig.suptitle(self.title)
        fig.patch.set_facecolor((0.6, 0.6, 0.6))
        bg_color = (0.5, 0.5, 0.5)
        plotted_labels = {}
        row = self.add_or_get_row("Portfolio Value", plotted_labels)
        ax[row].set_facecolor(bg_color)
        plots = {row: []}

        # # plot the data
        # fig = plt.figure(figsize=(10, 5))
        # ax = fig.add_axes([0.1, 0.2, 0.85, 0.7])
        # # customization of the axis
        # ax.spines['right'].set_color('none')
        # ax.spines['top'].set_color('none')
        # ax.xaxis.set_ticks_position('bottom')
        # ax.yaxis.set_ticks_position('left')
        # ax.tick_params(axis='both', direction='out', width=2, length=8,
        #                labelsize=12, pad=8)
        # ax.spines['left'].set_linewidth(2)
        # ax.spines['bottom'].set_linewidth(2)
        # # set the ticks of the x axis only when starting a new day
        # ax.set_xticks(data2[ndays[1], 0])
        # ax.set_xticklabels(xdays, rotation=45, horizontalalignment='right')
        #
        # ax.set_ylabel('Quote ($)', size=20)
        # ax.set_ylim([177, 196])
        #
        # candlestick(ax, data2, width=0.5, colorup='g', colordown='r')

        plots[0] += self.sub_plot(ax[row], "Portfolio Value", "Value", portfolio.data, self.get_next_color(), []) # '#f00', [])

        for symbol in self.collection.get_symbols():
            this_row = self.add_or_get_row("Price per {}".format(symbol), plotted_labels)
            self.candle_sub_plot(ax[this_row], self.price_plots[symbol], self.annotations)
            # plots[this_row] += self.series_sub_plot(ax[this_row], self.series, self.annotations)
            # Setting labels & titles
            ax[this_row].set_xlabel('Date')
            ax[this_row].set_ylabel('Price')
            ax[this_row].set_facecolor(bg_color)
            # fig.suptitle('Daily Candlestick Chart of NIFTY50')

        # Formatting Date
        # date_format = dates.DateFormatter('%d-%m-%Y')
        # ax[this_row].xaxis.set_major_formatter(date_format)
        fig.autofmt_xdate()

        for extra in self.extras:
            this_row = self.add_or_get_row(extra.label, plotted_labels)
            ax[this_row].set_facecolor(bg_color)
            # ax[this_row].set_title(extra.label)
            if this_row not in plots:
                plots[this_row] = []
            annotations = self.annotations
            adjust_annotations = True
            if adjust_annotations:
                for annotation in annotations:
                    annotation.y = extra.data.loc[annotation.x, :][0]
                    annotation.name += '({})'.format(annotation.y)
            plots[this_row] += self.sub_plot(ax[this_row], extra.name, extra.label, extra.data, extra.color, annotations)
        for row in plots.keys():
            labels = [plot.get_label() for plot in plots[row]]
            legend = ax[row].legend(plots[row], labels, loc=0)
            legend.get_frame().set_facecolor((0.6, 0.6, 0.6))
        # fig.tight_layout()
        fig.subplots_adjust(top=0.95, bottom=0.05, right=0.95, left=0.05)
        mng = plt.get_current_fig_manager()
        mng.full_screen_toggle()
        plt.show(block=block)

    def add_or_get_row(self, label, plotted_labels):
        if label not in plotted_labels:
            if plotted_labels:
                row = max(plotted_labels.values())
                plotted_labels[label] = row + 1
            else:
                plotted_labels[label] = 0
        return plotted_labels[label]

    def add_series_data(self, adapter: Adapter, portfolio):
        start: datetime = get_start_time(adapter.data)
        for value_type in adapter.request_value_types:
            # Time-series data...
            if value_type not in adapter.data:
                continue
            if value_type == ValueType.HIGH and self.draw_high_prices:
                self.add_to_prices(adapter.symbol, adapter, portfolio, start, self.get_next_color(),
                                   '{} High'.format(adapter.symbol), "Price per Unit", ValueType.HIGH)
            if value_type == ValueType.OPEN and self.draw_open_prices:
                self.add_to_prices(adapter.symbol, adapter, portfolio, start, self.get_next_color(),
                                   '{} Open'.format(adapter.symbol), "Price per Unit", ValueType.OPEN)
            if value_type == ValueType.OPEN and self.annotate_open_prices:
                self.add_to_annotate(adapter, portfolio, start, self.get_next_color(),  # '#00f',
                                     "o", ValueType.OPEN)
            if value_type == ValueType.CLOSE and self.annotate_close_prices:
                self.add_to_annotate(adapter, portfolio, start, self.get_next_color(),  # '#00f',
                                     "c", ValueType.CLOSE)
            if value_type == ValueType.LOW and self.draw_low_prices:
                self.add_to_prices(adapter.symbol, adapter, portfolio, start, self.get_next_color(),
                                   '{} Low'.format(adapter.symbol), "Price per Unit", ValueType.LOW)
            if value_type == ValueType.CLOSE and self.draw_close_prices:
                self.add_to_prices(adapter.symbol, adapter, portfolio, start, self.get_next_color(),
                                   '{} Close'.format(adapter.symbol), "Price per Unit", ValueType.CLOSE)
            # RSI data
            if value_type == ValueType.RSI:
                self.add_to_extras(adapter, portfolio, start, self.get_next_color(),  # '#00f',
                                   '{} RSI'.format(adapter.symbol), "RSI", ValueType.RSI)
            # MACD data
            if value_type == ValueType.MACD:
                self.add_to_extras(adapter, portfolio, start, self.get_next_color(),  # '#00f',
                                   '{} MACD'.format(adapter.symbol), "MACD", ValueType.MACD)
            if value_type == ValueType.MACD_SIGNAL:
                self.add_to_extras(adapter, portfolio, start, self.get_next_color(),  # '#00f',
                                   '{} MACD Signal'.format(adapter.symbol), "MACD", ValueType.MACD_SIGNAL)
            if value_type == ValueType.MACD_HIST:
                self.add_to_extras(adapter, portfolio, start, self.get_next_color(),  # '#00f',
                                   '{} MACD Histogram'.format(adapter.symbol), "MACD", ValueType.MACD_HIST)

    def add_to_annotate(self, adapter: Adapter, portfolio: Portfolio, start: datetime, color: Any, enumeration, value_type):
        data = adapter.get_column_on_or_after(start, value_type)
        if portfolio is not None:
            data = portfolio.filter_dict_times(data)
        self.annotate_values(enumeration, data, color)

    def add_to_extras(self, adapter: Adapter, portfolio: Portfolio, start: datetime, color: Any, title: str,
                      label: str, value_type: ValueType):
        data: pandas.Series = adapter.get_column_on_or_after(start, value_type)
        if portfolio is not None:
            data = portfolio.filter_dict_times(data)
        self.extras.append(Extra(title, data.to_frame(), color, label))

    def add_to_prices(self, symbol: str, adapter: Adapter,
                      portfolio: Optional[Portfolio], start: datetime, color: str,
                      title: str, label: str, value_type: ValueType):
        data: pandas.Series = adapter.get_column_on_or_after(start, value_type)
        if portfolio is not None:
            data = portfolio.filter_dict_times(data)
        self.add_to_price_plots(color, data, label, symbol)

    def add_to_price_plots(self, color: Any, data: pandas.Series, label: str, symbol: str):
        if symbol not in self.price_plots:
            frame: pandas.DataFrame = data.to_frame()
            frame = frame.sort_index(ascending=False)
            self.price_plots[symbol] = PricePlot(frame, color, label)
        else:
            # elif data.name in self.price_plots[symbol].data.columns.values:
            # Was dropping key, index here to keep:
            self.price_plots[symbol].data.loc[:, data.name] = data
            # self.price_plots[symbol].data = self.price_plots[symbol].data.merge(data, sort=True, how='outer',
            #                                     left_index=True, right_index=True,
            #                                     suffixes=('', '_dup'))
            # self.price_plots[symbol].data = self.price_plots[symbol].data.merge(data, sort=True, how='outer',
            #                                                                     left_index=True, right_index=True,
            #                                                                     suffixes=('', '_dup'))
            # Joining is working
            # self.price_plots[symbol].data = self.price_plots[symbol].data.join(data, sort=True, how="outer", rsuffix="-2")
            # (left.merge(right, on='key', how='outer', indicator=True)
            #  .query('_merge != "both"')
            #  .drop('_merge', 1))
        # else:
        #     self.price_plots[symbol].data = self.price_plots[symbol].data.join(data, sort=True)

    def plot_portfolios(self, block: bool = True):
        portfolio_count = len(self.portfolios)
        max_column_count = 2
        columns = max_column_count if portfolio_count >= max_column_count else portfolio_count
        rows = math.ceil(portfolio_count / max_column_count)
        fig, ax = plt.subplots(rows, columns, sharex='all')
        fig.suptitle(self.title)
        index = 0
        for portfolio in self.portfolios:
            for adapter in self.collection.adapters:
                # self.extras.clear()  # default is to add High and Low
                high_data = adapter.get_column(adapter.data, ValueType.HIGH)
                high = Extra('{} High'.format(adapter.symbol), high_data, '#aaf')
                high.label = "Price per Unit"
                self.extras.append(high)
                # close_data = adapter.dataAdapter.getSeriesData(adapter.symbol).getAllPrices(SeriesType.CLOSE)
                # self.extras.append(Extra('{} Close'.format(adapter.symbol), close_data, '#fad'))
                # open_data = adapter.dataAdapter.getSeriesData(adapter.symbol).getAllPrices(SeriesType.OPEN)
                # self.extras.append(Extra('{} Open'.format(adapter.symbol), open_data, '#afa'))
                low_data = adapter.get_column(adapter.data, ValueType.LOW)
                low = Extra('{} Low'.format(adapter.symbol), low_data, '#daf')
                low.label = "Price per Unit"
                self.extras.append(low)
            row = math.floor(index / columns) if (rows > 1) else 0
            column = index % columns
            if (rows == 1) and (columns == 1):
                self.plot(ax, portfolio.title, portfolio.data)
            elif rows == 1:
                self.plot(ax[column], portfolio.title, portfolio.data)
            else:
                self.plot(ax[row, column], portfolio.title, portfolio.data)
            index += 1
        mng = plt.get_current_fig_manager()
        mng.full_screen_toggle()
        plt.show(block=block)

    @staticmethod
    def split_data(data):
        keys = list(data.keys())
        values = list(data.values())
        return keys, values

    # @staticmethod
    # def stream_data(data):
    #     keys = list(data.keys())
    #     values = list(data.values())
    #     return keys, values

    def sub_plot(self, ax, title: str, label: str, data: pandas.DataFrame, color: str, annotations: List[
        Annotation]):
        row_count = data.shape[0]
        assert row_count > 0, "There is no data to plot"
        # times, values = self.split_data(data)
        # sorted_times = sorted(times)  # why sort?
        plots = ax.plot_date(data.index, data.values, '-', label=title, color=color)
        x_limits = [data.index.min(), data.index.max()]
        for annotation in annotations:
            ax.annotate(annotation.name,
                        xy=(annotation.x, annotation.y), xycoords='data',
                        xytext=(0, annotation.y_offset), textcoords='offset pixels',
                        arrowprops=dict(color=annotation.color, arrowstyle="->", connectionstyle="arc3"),
                        horizontalalignment='center',
                        verticalalignment='bottom')
        ax.set_xlim(x_limits)
        ax.set_ylabel(label)
        # ax.set_ylabel('Price')
        ax.set_xlabel('Date')
        return plots

    @staticmethod
    def candle_sub_plot(ax, series: PricePlot, annotations: List[Annotation]):
        prices = series.data
        label = series.label
        row_count = prices.shape[0]
        assert row_count > 0, "There is no data to plot"
        data = []
        price_dates = list(prices.index)
        for date in price_dates:
            row = prices.loc[date]
            data.append([dates.date2num(date), row[ValueType.OPEN], row[ValueType.CLOSE], row[ValueType.HIGH], row[ValueType.LOW]])
        width = (price_dates[1] - price_dates[0]) / timedelta(days=1.0) * 0.8
        candlestick_ochl(ax, data, width=width,
                         colorup='g',  # self.series[ValueType.HIGH].color,
                         colordown='r')  # self.series[ValueType.OPEN].color)
        for annotation in annotations:
            ax.annotate(annotation.name,
                        xy=(annotation.x, annotation.y), xycoords='data',
                        xytext=(0, annotation.y_offset), textcoords='offset pixels',
                        arrowprops=dict(color=annotation.color, arrowstyle="->", connectionstyle="arc3"),
                        horizontalalignment='center',
                        verticalalignment='bottom')
        ax.set_ylabel(label)
        ax.set_xlabel('Date')

    def plot(self, ax, title: str, data: Dict[datetime, float]):
        plots = []
        x_limits = []
        if data:
            investment_times, investment_values = self.split_data(data)
            sorted_times = sorted(investment_times)
            plots += ax.plot_date(investment_times, investment_values, '-', label='PortfolioValue', color='#f00')
            x_limits = [sorted_times[0], sorted_times[-1]]
        extra_labels = {}
        # for symbol, adapter in self.collection.symbolAdapters.items():
        for portfolio in self.portfolios:
            for extra in self.extras:
                times, values = self.split_data(extra.data)
                if not x_limits:
                    sorted_times = sorted(times)
                    x_limits = [sorted_times[0], sorted_times[-1]]
                if extra.share_y_axis:
                    plots += ax.plot_date(times, values, '-', label=extra.name, color=extra.color)
                else:
                    if extra.label not in extra_labels:
                        ax_new = ax.twinx()
                        ax_new.set_ylabel(extra.label, color=extra.labelColor)
                        extra_labels[extra.label] = ax_new
                    plots += extra_labels[extra.label].plot_date(times, values, '-', label=extra.name,
                                                                 color=extra.color)
            for annotation in self.annotations:
                ax_ano = extra_labels['Price per Unit'] if 'Price per Unit' in extra_labels else ax
                ax_ano.annotate(annotation.name,
                                xy=(annotation.x, annotation.y), xycoords='data',
                                xytext=(0, 20), textcoords='offset pixels',
                                arrowprops=dict(color=annotation.color, arrowstyle="->", connectionstyle="arc3"),
                                horizontalalignment='center',
                                verticalalignment='bottom')
        ax.set_xlim(x_limits)
        ax.set_ylabel('price')
        ax.set_xlabel('Date')
        labels = [plot.get_label() for plot in plots]
        ax.legend(plots, labels, loc=0)
        ax.set_title(title)

    def annotate_opened_order(self, order: Order):
        if not self.annotate_opened_orders:
            return
        name = 'o' + order.enumeration
        name += 's' if order.order_side == OrderSide.SELL else 'b'
        color = '#faa' if order.order_side == OrderSide.SELL else '#afa'
        price = round(order.price, 2)
        annotation = Annotation('{}:{:0.2f}'.format(name, price), order.open_time, price, color)
        annotation.y_offset = 40
        self.annotations.append(annotation)

    def annotate_closed_order(self, order: Order):
        if not self.annotate_closed_orders:
            return
        name = 'c' + order.enumeration
        name += 's' if order.order_side == OrderSide.SELL else 'b'
        color = '#f00' if order.order_side == OrderSide.SELL else '#0f0'
        price = round(order.price, 2)
        annotation = Annotation('{}:{:0.2f}'.format(name, price), order.close_time, price, color)
        annotation.y_offset = 20
        self.annotations.append(annotation)

    def annotate_canceled_order(self, order: Order) -> None:
        if not self.annotate_canceled_orders:
            return
        name = 'x' + order.enumeration
        name += 's' if order.order_side == OrderSide.SELL else 'b'
        color = '#a00' if order.order_side == OrderSide.SELL else '#0a0'
        price = round(order.price, 2)
        annotation = Annotation('{}:{:0.2f}'.format(name, price), order.close_time, price, color)
        annotation.y_offset = -50 if order.order_side == OrderSide.SELL else 40
        self.annotations.append(annotation)

    def annotate_values(self, enumeration: str, data: pandas.Series, color: str) -> None:
        for instance, value in data.items():
            annotation = Annotation('{}:{:0.2f}'.format(enumeration, value), instance, value, color)
            self.annotations.append(annotation)


