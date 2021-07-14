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
import pickle
import sys
from argparse import ArgumentParser
from datetime import datetime

import yaml

from main.common.fileSystem import FileSystem
from main.common.profiler import Profiler
from main.common.report import Report
from main.runners.runner import Runner


class NoSymbolsSpecifiedException(RuntimeError):
    pass


def read_pkl_config_file(config_path: str) -> Runner:
    return pickle.load(open(config_path))


def read_yaml_config_file(runner: Runner, config_path: str) -> None:
    logging.debug(f"Reading YAML config file: file://{config_path}")
    with open(config_path) as infile:
        config = yaml.safe_load(infile)
        runner.symbols = config['symbols']
        if not runner.symbols:
            raise NoSymbolsSpecifiedException(f"Please specify at least one symbol in: {config_path}")
        class_name = config['adapter_class']
        # intrinsic_value.adapter_class = getattr(
        runner.adapter_class = getattr(
            sys.modules[f'main.adapters.thirdPartyShims.{class_name[0].lower()}{class_name[1:]}'], f'{class_name}')
        # self.adapter_class = getattr(sys.modules[__name__], class_name)
        runner.base_symbol = config['base_symbol']


# def write_pkl_config_file(runner: Runner) -> None:
#     config_path = get_output_pkl_config_path(runner.run_name)
#     pickle.dump(runner, open(config_path, 'wb'))


def write_yaml_config_file(runner: Runner) -> None:
    output_dir = FileSystem.get_output_dir(Report.camel_to_snake(runner.__class__.__name__))
    config_path = os.path.join(output_dir, f"{runner.get_run_name()}.yaml")
    # config_path = get_output_yaml_config_path(runner.run_name)
    logging.debug(f"Writing YAML config file: file://{config_path}")
    with open(config_path, 'w') as outfile:
        yaml.dump(runner.get_config(), outfile, default_flow_style=False)


class Launcher:
    def __init__(self, runner):
        self.runner = runner

    def run(self, args) -> bool:
        if args.profile:
            Profiler.get_instance().enable()
        Launcher.configure_logging(args.debug)
        Launcher.print_copyright_notice()
        Launcher.check_environment()
        success = True
        run_start = datetime.now()
        if 'config_path' in args:
            read_yaml_config_file(self.runner, args.config_path)
        success = success and self.runner.start()
        if 'config_path' in args:
            write_yaml_config_file(self.runner)
        run_end = datetime.now()
        logging.info(">> Running took: {}s".format(run_end - run_start))
        if Profiler.instance is not None:  # if get_instance hasn't been called yet, then don't do the reporting
            Profiler.get_instance().disable_and_report()
        return success

    @staticmethod
    def add_common_arguments(parser: ArgumentParser) -> None:
        parser.add_argument("-d", "--debug", action="store_true",
                            help="Print debug messages to console")
        parser.add_argument("-p", "--profile", action="store_true",
                            help="Profile the run")
        parser.add_argument("-c", "--cache-dir", dest='cache_dir', type=str, default=FileSystem.parent_cache_dir,
                            help=f"Write cache files to the specified location")
        parser.add_argument("-o", "--output-dir", dest='output_dir', type=str, default=FileSystem.parent_output_dir,
                            help=f"Write output files to the specified location")

    @classmethod
    def add_input_config_argument(cls, parser: ArgumentParser, default: str) -> None:
        parser.add_argument("-i", "--input-config", dest='config_path', type=str, default=default,
                            help=f"Read config file from the specified location")

    @staticmethod
    def configure_logging(console_debug: bool):
        logging.getLogger().setLevel(logging.DEBUG)
        out_handler = logging.StreamHandler(sys.stdout)
        out_handler.setLevel(logging.DEBUG if console_debug else logging.INFO)
        out_handler.setFormatter(logging.Formatter("%(message)s"))
        logging.getLogger().addHandler(out_handler)
        # script_dir = os.path.dirname(os.path.realpath(__file__))
        cache_dir = FileSystem.get_and_clean_timestamp_dir(FileSystem.get_cache_dir('runs'))
        run_log = os.path.join(cache_dir, 'run.log')
        file_handler = logging.FileHandler(run_log)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter("%(levelname)-5s: %(message)-320s %(asctime)s %(threadName)s"))
        logging.getLogger().addHandler(file_handler)
        logging.info(">> Run log: {}".format(FileSystem.file_link_format(run_log)))

    @staticmethod
    def print_copyright_notice():
        current_year = Launcher.get_current_copyright_year()
        original_year = 2021
        year_string = str(original_year) if current_year == original_year else f"{original_year}-{current_year}"
        logging.info(f"Finance from eContriver (C) {year_string} eContriver LLC")
        logging.info("This program comes with ABSOLUTELY NO WARRANTY; for details see the GNU GPL v3.")
        logging.info("This is free software, and you are welcome to redistribute it under certain conditions.")

    @staticmethod
    def get_current_copyright_year():
        """
        The year is not calculated as the copyright should only state the dates for which it was released.
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

