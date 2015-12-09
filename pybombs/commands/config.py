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
import argparse
from pybombs.commands import CommandBase
from pybombs.config_manager import extract_cfg_items

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

    def __init__(self, cmd, args):
        CommandBase.__init__(self,
            cmd, args,
            load_recipes=False,
            require_prefix=False,
            require_inventory=False,
        )
        # Figure out which config file to write to
        self.cfg_file = self.cfg.local_cfg
        prefix = self.cfg.get_active_prefix()
        if self.args.config_file is not None:
            self.cfg_file = self.args.config_file
        elif prefix.prefix_dir is not None and prefix.prefix_src == "cli":
            self.cfg_file = prefix.cfg_file
        self.log.debug("Using config file: {0}".format(self.cfg_file))

    def run(self):
        """ Go, go, go! """
        print_key = lambda k: print(
            "{key}: {value}".format(
                key=k, value=self.cfg.get(k, "")
            )
        )
        cfg_data = extract_cfg_items(self.cfg_file, 'config', False)
        if self.args.key is None:
            if self.args.config_only:
                for key in cfg_data.keys():
                    print("{0}: {1}".format(key, cfg_data.get(key)))
            else:
                for key in self.cfg.get_all_keys():
                    print_key(key)
            return
        # Show one config item:
        if self.args.value is None:
            if self.args.config_only:
                print("{0}: {1}".format(self.args.key, cfg_data.get(self.args.key)))
            else:
                print_key(self.args.key)
            key_help = self.cfg.get_help(self.args.key)
            if key_help:
                print("  - {help}".format(help=key_help))
            return
        # If both are given, update the config file
        self.cfg.update_cfg_file(
            new_data={'config': {self.args.key: self.args.value}},
            cfg_file=self.cfg_file,
        )

