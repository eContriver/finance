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

from enum import Enum, auto
from typing import List

import pandas

from main.application.adapter import insert_column
from main.application.runner import Runner
from main.application.strategy import Strategy
from main.common.report import Report, to_percent, to_dollars


class StrategyResultsAreEmptyException(RuntimeError):
    pass


class SymbolRunner(Runner):

    @staticmethod
    def summarize(title, strategies: List[Strategy], report: Report):
        """
        Summarizes the results of a multi-symbol run
        :param report: the report object that will be used to create the on-disk report
        :param title: The title of the run, printed as a header of the output
        :param strategies: A list of the different strategies (that were run) to report on
        """
        report.log('== {}'.format(title))
        # logging.info('== {}'.format(title))
        names = []
        cagrs = []
        rois = []
        end_values = []
        start_dates = []
        end_dates = []
        for strategy in strategies:
            if strategy is None:
                # logging.info("{:>100}".format("Failed to retrieve strategy data, perhaps an error occurred."))
                report.log("{:>100}".format("Failed to retrieve strategy data, perhaps an error occurred."))
            else:
                names.append(str(strategy))
                cagrs.append(strategy.portfolio.calculate_cagr())
                rois.append(strategy.portfolio.calculate_roi())
                end_values.append(strategy.portfolio.get_latest_value())
                start_dates.append(strategy.portfolio.get_first_completed_date())
                end_dates.append(strategy.portfolio.get_last_completed_date())

        df: pandas.DataFrame = pandas.DataFrame()
        insert_column(df, ColumnType.CAGR, names, cagrs)
        insert_column(df, ColumnType.ROI, names, rois)
        insert_column(df, ColumnType.END_VALUE, names, end_values)
        insert_column(df, ColumnType.START_DATE, names, start_dates)
        insert_column(df, ColumnType.END_DATE, names, end_dates)
        report_df = report_format(df)
        report.log("{}".format(report_df.to_string()))


class ColumnType(Enum):
    STRATEGY_NAME = auto()
    CAGR = auto()
    ROI = auto()
    END_VALUE = auto()
    START_DATE = auto()
    END_DATE = auto()

    def __str__(self):
        return self.as_title()

    def as_title(self):
        return self.name.replace('_', ' ')


def report_format(df_orig):
    df = df_orig.copy()
    convert_formats(df)
    df = report_order(df)
    return df


def report_order(df):
    # columns = [ColumnType.STRATEGY_NAME]
    columns = [ColumnType.CAGR]
    columns += [ColumnType.ROI]
    columns += [ColumnType.END_VALUE]
    columns += [ColumnType.START_DATE]
    columns += [ColumnType.END_DATE]
    df_ordered = df[columns]  # reorders using order of columns
    return df_ordered


def convert_formats(df: pandas.DataFrame):
    # df[ColumnType.STRATEGY_NAME] = df[ColumnType.STRATEGY_NAME]
    df[ColumnType.CAGR] = df[ColumnType.CAGR].apply(to_percent)
    df[ColumnType.ROI] = df[ColumnType.ROI].apply(to_percent)
    df[ColumnType.END_VALUE] = df[ColumnType.END_VALUE].apply(to_dollars)


def get_first_time(strategy):
    date_format: str = '%Y-%m-%d'
    first_time = strategy.portfolio.get_first_completed_time()
    first_time = first_time if first_time is None else first_time.strftime(date_format)
    return first_time


def get_last_time(strategy):
    date_format: str = '%Y-%m-%d'
    last_time = strategy.portfolio.get_last_completed_time()
    last_time = last_time if last_time is None else last_time.strftime(date_format)
    return last_time
