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
import os
from pathlib import Path


class SharedLocations:

    def __init__(self):
        script_dir = os.path.dirname(os.path.realpath(__file__))
        self.parent_cache_dir = os.path.realpath(os.path.join(script_dir, '..', '..', '..', '.cache'))
        self.parent_output_dir = os.path.realpath(os.path.join(script_dir, '..', '..', '..', 'output'))
        self.parent_user_dir = os.path.realpath(os.path.join(str(Path.home()), '.eContriver'))

    def get_cache_dir(self, name):
        cache_dir = os.path.join(self.parent_cache_dir, name)
        return cache_dir

    def get_output_dir(self, name):
        output_dir = os.path.join(self.parent_output_dir, name)
        return output_dir

    def get_parent_user_dir(self):
        return self.parent_user_dir

