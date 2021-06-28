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


from typing import Optional, List

import pandas

from main.visual.annotation import Annotation


class Extra:
    def __init__(self, name: str, data: pandas.DataFrame, color, label: Optional[str] = None,
                 share_y_axis: bool = False, as_candlesticks: bool = False):
        self.color = color
        self.data = data
        self.label = name if label is None else label
        self.labelColor = 'black'
        self.name = name
        self.share_y_axis = share_y_axis
        self.as_candlesticks = as_candlesticks
        self.annotations: List[Annotation] = []  # HasAnnotations decorator?
