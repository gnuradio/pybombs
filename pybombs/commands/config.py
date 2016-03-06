#
# Copyright 2015 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
#
# GNU Radio is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# GNU Radio is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GNU Radio; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#
""" PyBOMBS command: config """

from __future__ import print_function
from pybombs.commands import CommandBase
from pybombs.config_manager import extract_cfg_items
from pybombs.config_file import PBConfigFile

class Config(CommandBase):
    """ Remove a package from this prefix """
    cmds = {
        'config': 'Query or update configuration',
    }

    @staticmethod
    def setup_subparser(parser, cmd=None):
        """
        Set up a subparser for 'config'
        """
        parser.add_argument(
            'key', nargs='?',
            help="Configuration key to query or set",
        )
        parser.add_argument(
            'value', nargs='?',
            help="New value",
        )
        parser.add_argument(
            '-c', '--config-file',
            help="Specify the config file to update",
        )
        parser.add_argument(
            '-o', '--config-only', action='store_true',
            help="If specified, only consider options from this one file. Default: Consider all config options",
        )
        parser.add_argument(
            '-P', '--package',
            help="If specified, set options for this package instead of the global configs",
        )
        parser.add_argument(
            '-C', '--category',
            help="If specified, set options for this category instead of the global configs",
        )

    def __init__(self, cmd, args):
        CommandBase.__init__(self,
            cmd, args,
            load_recipes=False,
            require_prefix=False,
        )
        # Figure out which config file to write to
        self.cfg_file = self.cfg.local_cfg
        prefix = self.cfg.get_active_prefix()
        if self.args.config_file is not None:
            self.cfg_file = self.args.config_file
        elif prefix.prefix_dir is not None and prefix.prefix_src == "cli":
            self.cfg_file = prefix.cfg_file
        self.log.info("Using config file: {0}".format(self.cfg_file))

    def run(self):
        " Go, go, go! "
        if self.args.package is not None or self.args.category is not None:
            return self._run_pkg_or_cat()
        return self._run_config()

    def _run_config(self):
        """
        Handle `pybombs config'
        """
        if self.args.config_only:
            cfg_data = extract_cfg_items(self.cfg_file, 'config', False)
        else:
            cfg_data = self.cfg
        keys = [self.args.key]
        if self.args.key is None:
            keys = cfg_data.keys()
        elif self.args.value is not None:
            self.cfg.set(self.args.key, self.args.value)
            self.cfg.update_cfg_file(
                new_data={'config': {self.args.key: self.args.value}},
                cfg_file=self.cfg_file,
            )
        for key in keys:
            print("{key}: {value}".format(key=key, value=cfg_data.get(key, "")))
            print("  - {help}".format(help=self.cfg.get_help(key) or " Undocumented config option"))

    def _run_pkg_or_cat(self):
        """
        Handle `pybombs config --package or --category'
        """
        if self.args.package is not None and self.args.category is not None:
            self.log.error("Cannot provide both --package and --category!")
            return -1
        if self.args.package is not None:
            config_target = 'packages'
            pkg_cat = self.args.package
        elif self.args.category is not None:
            config_target = 'categories'
            pkg_cat = self.args.category
        cfg_file = PBConfigFile(self.cfg_file)
        keys = [self.args.key]
        verb = "Getting"
        if self.args.key is None:
            keys = cfg_file.data.get(config_target, {}).get(pkg_cat, {}).keys()
        elif self.args.value is not None:
            cfg_file.update({config_target: {pkg_cat: {self.args.key: self.args.value}}})
            verb = "Setting"
        print("{verb} keys for {target} {pkgcat}:".format(verb=verb, target=config_target, pkgcat=pkg_cat))
        for key in keys:
            print("{key}: {value}".format(
                key=key,
                value=cfg_file.data.get(config_target, {}).get(pkg_cat, {}).get(key))
            )

