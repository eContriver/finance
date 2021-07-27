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
import importlib
import logging
import os
import sys
from argparse import ArgumentParser
from datetime import datetime
from typing import List

import yaml

from main.common.profiler import Profiler
from main.common.report import Report
from main.common.locations import Locations, get_and_clean_timestamp_dir, file_link_format
from main.application.runner import Runner


def read_yaml_config_file(config_path: str):
    """
    Read a YAML file into a Python data structure that can be used to access the data and set properties of objects.
    This method uses the safe_load method which is known to be safe with unknown YAML files. This means that we have to
    manually translate arguments (like Adapters class names) from strings into the objects, but this prevents malicious
    actors from being able to inject executable snippets into the YAML and then sharing it with others.
    :param config_path: The location of the YAML file that will be read
    :return: The Python representation of the data that was read from the YAML file
    """
    logging.debug(f"Reading YAML config file: file://{config_path}")
    with open(config_path) as infile:
        config = yaml.safe_load(infile)
    return config


def write_yaml_config_file(output_dir: str, runner: Runner) -> None:
    """
    Write a YAML file with the configuration of a Runner. This is generally used to write the arguments of a run next to
    the report of a run for reproducibility and for sharing purposes.
    :param output_dir: The location that the YAML file will be written to - file name is the (Runners) run name
    :param runner: The runner to be serialized into a YAML file
    :return:
    """
    config_path = os.path.join(output_dir, f"{runner.get_run_name()}.yaml")
    logging.debug(f"Writing YAML config file: file://{config_path}")
    output_dir: str = os.path.dirname(config_path)
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    with open(config_path, 'w') as outfile:
        yaml.dump(runner.get_config(), outfile, default_flow_style=False)


def load_adapters():
    """
    Add all modules in the adapters directory
    :return:
    """
    adapter_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'adapters'))
    for module in os.listdir(adapter_dir):
        if module == '__init__.py' or module[-3:] != '.py':
            continue
        importlib.import_module(f'.{module[:-3]}', f'main.adapters')
    del module


class MissingConfigKeyException(KeyError):
    """
    This exception is thrown while parsing YAML configuration files and just adds the currently processing configur
    file to the error message.
    """
    pass


def configure_logging(cache_dir: str, console_debug: bool) -> None:
    """
    Configures the default logging variable with DEBUG going to the .cache/run output file by default (even if -d is not
    set). The STDOUT will be set to INFO messages by default. The DEBUG logs will have the timestamps and threads added
    to them, but those are added to the far right in the log file so the messages are easily viewed without having to
    scroll. If the timestamps are needed, then scroll.
    :param cache_dir: This is used to write the out (with debug messages) to by default
    :param console_debug: This boolean can be used to toggle the printing of debug messages in the console/STDOUT
    :return:
    """
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


def get_copyright_notice() -> List[str]:
    """
    Returns the standard copyright that is printed to the top of reports and at the beginning of program execution.
    :return: A list of strings where each entry is intended to be a single line in a report or on the console
    """
    current_year = get_current_copyright_year()
    original_year = 2021
    year_string = str(original_year) if current_year == original_year else f"{original_year}-{current_year}"
    return [
        f"Finance from eContriver (C) {year_string} eContriver LLC",
        "This program comes with ABSOLUTELY NO WARRANTY; for details see the GNU GPL v3.",
        "This is free software, and you are welcome to redistribute it under certain conditions."
    ]


def print_copyright_notice() -> None:
    """
    Prints the copyright to the logging info output which is generally configured to be STDOUT and prints by default.
    :return:
    """
    copyright_notice = get_copyright_notice()
    for line in copyright_notice:
        logging.info(line)


def get_current_copyright_year() -> int:
    """
    The year is not calculated as the copyright should only state the dates for which it was released. This function
    just makes it so we can update all copyright references from one place.
    :return: The current year
    """
    return 2021


def check_environment() -> None:
    """
    Checks that the environment is setup as expected. If not, then exceptions or warnings can be thrown.
    :return:
    """
    if os.environ.get('DISPLAY') is None:
        logging.warning(
            "The DISPLAY environment variable is not set - this is used for x11 forwarding from the docker "
            "container to the host machine for the plots.")
    else:
        logging.debug("Using display: {}".format(os.environ.get('DISPLAY')))


class Launcher:
    """
    The intent of this class is to act as a common launcher for all of the different invocation points.
    """

    def __init__(self, runner):
        self.runner = runner

    def run(self, locations: Locations, args) -> bool:
        cache_dir = get_and_clean_timestamp_dir(locations.get_cache_dir('runs'))
        configure_logging(cache_dir, args.debug)
        print_copyright_notice()
        check_environment()
        if args.profile:
            Profiler.get_instance().enable()
        success = True
        run_start = datetime.now()
        load_adapters()
        if 'config_path' in args:
            config = read_yaml_config_file(args.config_path)
            try:
                self.runner.set_from_config(config, args.config_path)
            except KeyError as e:
                raise MissingConfigKeyException(f"While parsing {file_link_format(args.config_path)} failed to find "
                                                f"expected key: {e}")
        success = success and self.runner.start(locations)
        if 'config_path' in args:
            output_dir = locations.get_output_dir(Report.camel_to_snake(self.runner.__class__.__name__))
            write_yaml_config_file(output_dir, self.runner)
        run_end = datetime.now()
        logging.info(">> Running took: {}s".format(run_end - run_start))
        if args.profile:
            # profile_log = os.path.join(cache_dir, 'profile.log')
            Profiler.get_instance().disable_and_report()
            Profiler.get_instance().dump_stats()
        return success

    @classmethod
    def add_common_arguments(cls, parser: ArgumentParser, default_cache_dir: str, default_output_dir: str) -> None:
        """
        Add arguments only for runs that support configuration files.
        :param parser: The ArgumentParser class that the arguments are added to
        :param default_output_dir: The default output file location
        :param default_cache_dir: The default cache file location
        :return:
        """
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
        """
        Add arguments only for runs that support configuration files.
        :param parser: The ArgumentParser class that the arguments are added to
        :param default_config_file: The default configuration file location
        :return:
        """
        group_config = parser.add_argument_group('configuration arguments')
        group_config.add_argument("-i", "--input-config", dest='config_path', type=str, default=default_config_file,
                                  help=f"Read config file from the specified location")
