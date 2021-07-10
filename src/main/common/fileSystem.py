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
from pathlib import Path
from typing import Optional


class FileSystem:
    script_dir = os.path.dirname(os.path.realpath(__file__))
    parent_cache_dir = os.path.realpath(os.path.join(script_dir, '..', '..', '..', '.cache'))
    parent_output_dir = os.path.realpath(os.path.join(script_dir, '..', '..', '..', 'output'))
    parent_user_dir = os.path.realpath(os.path.join(str(Path.home()), '.eContriver'))

    @staticmethod
    def get_cache_dir(name):
        cache_dir = os.path.join(FileSystem.parent_cache_dir, name)
        return cache_dir

    @staticmethod
    def get_output_dir(name):
        output_dir = os.path.join(FileSystem.parent_output_dir, name)
        return output_dir

    @staticmethod
    def get_parent_user_dir():
        return FileSystem.parent_user_dir

    @staticmethod
    def get_and_clean_timestamp_dir(root_dir, date_format: Optional[str] = "%Y%m%d_%H%M%S"):
        FileSystem.clean_dir(root_dir)
        cache_dir = root_dir if date_format is None else os.path.join(root_dir, datetime.now().strftime(date_format))
        cache_dir = os.path.realpath(cache_dir)
        os.makedirs(cache_dir)
        return cache_dir

    @staticmethod
    def clean_dir(output_dir, keep: int = 3, ignore_errors: bool = True):
        if not os.path.exists(output_dir):
            return
        children = sorted(Path(output_dir).iterdir(), key=os.path.getmtime)
        for filename in children[:-keep]:
            path = os.path.join(output_dir, filename)
            shutil.rmtree(path, ignore_errors)

    @staticmethod
    def file_link_format(profile_log) -> str:
        # This syntax was not working with the default run console until [X] Run with Python Console was checked
        return "file://{}".format(str(profile_log))
        # The following only works if the file already exists... which most of the time the log isn't created until
        # after the process is nearly complete so this won't work
        # return f"""File "{profile_log}", line 1, in log"""
