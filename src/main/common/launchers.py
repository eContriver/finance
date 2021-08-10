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
from datetime import datetime

from main.common.profiler import Profiler
from main.common.report import Report
from main.common.locations import Locations, get_and_clean_timestamp_dir, file_link_format
from main.application.runner import read_yaml_config_file, write_yaml_config_file, load_adapters, \
    configure_logging, print_copyright_notice, check_environment


class MissingConfigKeyException(KeyError):
    """
    This exception is thrown while parsing YAML configuration files and just adds the currently processing configur
    file to the error message.
    """
    pass


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


