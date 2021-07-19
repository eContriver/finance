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
import argparse
import importlib
import logging
import os
import sys
from argparse import ArgumentParser
from datetime import datetime

import yaml

from main.common.profiler import Profiler
from main.common.report import Report
from main.common.locations import Locations, get_and_clean_timestamp_dir, file_link_format
from main.runners.runner import Runner


def read_yaml_config_file(config_path: str):
    logging.debug(f"Reading YAML config file: file://{config_path}")
    with open(config_path) as infile:
        config = yaml.safe_load(infile)
    return config


def write_yaml_config_file(output_dir: str, runner: Runner) -> None:
    config_path = os.path.join(output_dir, f"{runner.get_run_name()}.yaml")
    logging.debug(f"Writing YAML config file: file://{config_path}")
    output_dir: str = os.path.dirname(config_path)
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    with open(config_path, 'w') as outfile:
        yaml.dump(runner.get_config(), outfile, default_flow_style=False)


def add_third_party_adapters():
    """
    Add all modules in the third_party_shims directory
    :return:
    """
    ext_adapter_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'adapters', 'third_party_shims'))
    for module in os.listdir(ext_adapter_dir):
        if module == '__init__.py' or module[-3:] != '.py':
            continue
        importlib.import_module(f'.{module[:-3]}', f'main.adapters.third_party_shims')
    del module


class Launcher:
    def __init__(self, runner):
        self.runner = runner

    def run(self, locations: Locations, args) -> bool:
        cache_dir = get_and_clean_timestamp_dir(locations.get_cache_dir('runs'))
        Launcher.configure_logging(cache_dir, args.debug)
        Launcher.print_copyright_notice()
        Launcher.check_environment()
        if args.profile:
            Profiler.get_instance().enable()
        success = True
        run_start = datetime.now()
        add_third_party_adapters()
        if 'config_path' in args:
            config = read_yaml_config_file(args.config_path)
            self.runner.set_from_config(config, args.config_path)
        success = success and self.runner.start(locations)
        if 'config_path' in args:
            output_dir = locations.get_output_dir(Report.camel_to_snake(self.runner.__class__.__name__))
            write_yaml_config_file(output_dir, self.runner)
        run_end = datetime.now()
        logging.info(">> Running took: {}s".format(run_end - run_start))
        if Profiler.instance is not None:  # if get_instance hasn't been called yet, then don't do the reporting
            profile_log = os.path.join(cache_dir, 'profile.log')
            Profiler.get_instance().disable_and_report(profile_log)
        return success

    @classmethod
    def add_common_arguments(cls, parser: ArgumentParser, default_cache_dir: str, default_output_dir: str) -> None:
        parser.add_argument("-d", "--debug", action="store_true",
                            help="Print debug messages to console")
        parser.add_argument("-p", "--profile", action="store_true",
                            help="Profile the run")
        parser.add_argument("-c", "--cache-dir", dest='cache_dir', type=str, default=default_cache_dir,
                            help=f"Write cache files to the specified location")
        parser.add_argument("-o", "--output-dir", dest='output_dir', type=str, default=default_output_dir,
                            help=f"Write output files to the specified location")

    @classmethod
    def add_config_arguments(cls, parser: ArgumentParser, default_config_file: str) -> None:
        group_config = parser.add_argument_group('configuration options')
        group_config.add_argument("-i", "--input-config", dest='config_path', type=str, default=default_config_file,
                                  help=f"Read config file from the specified location")

    @staticmethod
    def configure_logging(cache_dir: str, console_debug: bool):
        logging.getLogger().setLevel(logging.DEBUG)
        out_handler = logging.StreamHandler(sys.stdout)
        out_handler.setLevel(logging.DEBUG if console_debug else logging.INFO)
        out_handler.setFormatter(logging.Formatter("%(message)s"))
        logging.getLogger().addHandler(out_handler)
        run_log = os.path.join(cache_dir, 'run.log')
        file_handler = logging.FileHandler(run_log)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter("%(levelname)-5s: %(message)-320s %(asctime)s %(threadName)s"))
        logging.getLogger().addHandler(file_handler)
        logging.info(">> Run log: {}".format(file_link_format(run_log)))

    @staticmethod
    def get_copyright_notice():
        current_year = Launcher.get_current_copyright_year()
        original_year = 2021
        year_string = str(original_year) if current_year == original_year else f"{original_year}-{current_year}"
        return [
            f"Finance from eContriver (C) {year_string} eContriver LLC",
            "This program comes with ABSOLUTELY NO WARRANTY; for details see the GNU GPL v3.",
            "This is free software, and you are welcome to redistribute it under certain conditions."
        ]

    @staticmethod
    def print_copyright_notice():
        copyright_notice = Launcher.get_copyright_notice()
        for line in copyright_notice:
            logging.info(line)

    @staticmethod
    def get_current_copyright_year():
        """
        The year is not calculated as the copyright should only state the dates for which it was released. This function
        just makes it so we can update all copyright references from one place.
        :return: The current year
        """
        return 2021

    @staticmethod
    def check_environment():
        if os.environ.get('DISPLAY') is None:
            raise RuntimeError(
                "The DISPLAY environment variable is not set - this is used for x11 forwarding from the docker "
                "container to the host machine for the plots.")
        else:
            logging.debug("Using display: {}".format(os.environ.get('DISPLAY')))

