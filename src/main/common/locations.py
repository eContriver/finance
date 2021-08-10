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
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional


def get_parent_cache_dir() -> str:
    """
    Get the default cache cache directory, it is considered a parent because subfolders are created inside of it.
    :return: The parent cache directory
    """
    script_dir = os.path.dirname(os.path.realpath(__file__))
    parent_cache_dir = os.path.realpath(os.path.join(script_dir, '..', '..', '..', '.cache'))
    return parent_cache_dir


def get_parent_output_dir() -> str:
    """
    Get the default output output directory, it is considered a parent because subfolders are created inside of it.
    :return: The parent output directory
    """
    script_dir = os.path.dirname(os.path.realpath(__file__))
    parent_output_dir = os.path.realpath(os.path.join(script_dir, '..', '..', '..', 'output'))
    return parent_output_dir


def get_parent_user_dir() -> str:
    """
    Get the default user user directory, it is considered a parent because subfolders are created inside of it.
    :return: The parent user directory
    """
    parent_user_dir = os.path.realpath(os.path.join(str(Path.home()), '.eContriver'))
    return parent_user_dir


class Locations:

    def __init__(self):
        script_dir = os.path.dirname(os.path.realpath(__file__))
        self.parent_cache_dir = os.path.realpath(os.path.join(script_dir, '..', '..', '..', '.cache'))
        self.parent_output_dir = os.path.realpath(os.path.join(script_dir, '..', '..', '..', 'output'))
        self.parent_user_dir = os.path.realpath(os.path.join(str(Path.home()), '.eContriver'))

    def get_cache_dir(self, name: str) -> str:
        """
        Get the default cache cache directory, it is considered a parent because subfolders are created inside of it.
        :return: The parent cache directory
        """
        cache_dir = os.path.join(self.parent_cache_dir, name)
        return cache_dir

    def get_output_dir(self, name):
        """
        Get the default output output directory, it is considered a parent because subfolders are created inside of it.
        :return: The parent output directory
        """
        output_dir = os.path.join(self.parent_output_dir, name)
        return output_dir

    def get_parent_user_dir(self):
        """
        Get the default user user directory, it is considered a parent because subfolders are created inside of it.
        :return: The parent user directory
        """
        return self.parent_user_dir


def get_and_clean_timestamp_dir(root_dir, date_format: Optional[str] = "%Y%m%d_%H%M%S"):
    preserve_pattern = '.cache'
    if preserve_pattern in root_dir:
        clean_dir(root_dir)
    else:
        logging.warning(f'Will not clean {root_dir} as it does not match pattern {preserve_pattern}')
    cache_dir = root_dir if date_format is None else os.path.join(root_dir, datetime.now().strftime(date_format))
    cache_dir = os.path.realpath(cache_dir)
    os.makedirs(cache_dir)
    return cache_dir


def clean_dir(output_dir: dir, keep: int = 3, ignore_errors: bool = True):
    if not os.path.exists(output_dir):
        return
    children = sorted(Path(output_dir).iterdir(), key=os.path.getmtime)
    for filename in children[:-keep]:
        path = os.path.join(output_dir, filename)
        shutil.rmtree(path, ignore_errors)


def file_link_format(profile_log: str) -> str:
    # This syntax was not working with the default run console until [X] Run with Python Console was checked
    return "file://{}".format(str(profile_log))
    # The following only works if the file already exists... which most of the time the log isn't created until
    # after the process is nearly complete so this won't work
    # return f"""File "{profile_log}", line 1, in log"""
