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
import re
import shutil
from datetime import datetime
from typing import Optional


class FileSystem:

    @staticmethod
    def get_and_clean_cache_dir(root_dir, date_format: Optional[str] = "%Y%m%d_%H%M%S"):
        FileSystem.clean_cache_dirs(root_dir)
        cache_dir = root_dir if date_format is None else os.path.join(root_dir, datetime.now().strftime(date_format))
        cache_dir = os.path.realpath(cache_dir)
        os.makedirs(cache_dir)
        return cache_dir

    @staticmethod
    def clean_cache_dirs(cache_dir, keep: int = 3, ignore_errors: bool = True):
        if not os.path.exists(cache_dir):
            return
        for filename in sorted(os.listdir(cache_dir))[:-keep]:
            path = os.path.join(cache_dir, filename)
            shutil.rmtree(path, ignore_errors)

    @staticmethod
    def file_link_format(profile_log) -> str:
        # This syntax was not working with the default run console until [X] Run with Python Console was checked
        return "file://{}".format(str(profile_log))
        # The following only works if the file already exists... which most of the time the log isn't created until
        # after the process is nearly complete so this won't work
        # return f"""File "{profile_log}", line 1, in log"""
