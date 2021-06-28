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

from typing import Any, List

from main.adapters.valueType import ValueType


class Converter:
    value_type: ValueType
    get_response_callback: Any
    response_keys: List[str]
    adjust_values: bool

    def __init__(self, value_type: ValueType, get_response_callback: Any, response_keys: List[str],
                 adjust_values: bool = False):
        self.value_type = value_type
        self.get_response_callback = get_response_callback
        self.response_keys = response_keys
        self.adjust_values = adjust_values