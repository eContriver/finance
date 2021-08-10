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

from unittest import TestCase

from main.application.adapter import AssetType
from main.application.runner import get_asset_type_overrides


class Test(TestCase):
    def test_get_asset_type_overrides(self):
        """
        Test that the get asset overrides method will correctly convert asset type strings to their enumeration
        :return:
        """
        for asset_type in AssetType:
            self.assertEqual(get_asset_type_overrides({'TEST': asset_type.name}), {'TEST': asset_type})
