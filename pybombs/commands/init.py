#!/usr/bin/env python2
#
# Copyright 2015 Free Software Foundation, Inc.
#
# This file is part of PyBOMBS
#
# PyBOMBS is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# PyBOMBS is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyBOMBS; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#
""" PyBOMBS command: init """

import os
import pprint
from pybombs.commands import CommandBase

class Init(CommandBase):
    """
    Prefix init operations.
    """
    cmds = {
        'init': 'Init command', # TODO nicer
    }

    @staticmethod
    def setup_subparser(parser, cmd=None):
        """
        Set up a subparser for 'install'
        """
        parser.add_argument(
                'prefix',
                help="Prefix to initialize",
                action='store',
                default="",
                nargs='*'
        )

    def __init__(self, cmd, args):
        CommandBase.__init__(self,
                cmd, args,
                load_recipes=False,
                require_prefix=False,
                require_inventory=False
        )

    def run(self):
        """ Go, go, go! """
        new_prefix = os.getcwd()
        if self.args.prefix:
            new_prefix = self.args.prefix[0]
        if not os.path.isdir(new_prefix):
            self.log.error("{} is not a valid directory! Unable in initialize pybombs prefix".format(new_prefix))
            return
        self.log.debug("Initializing new prefix directory in {0}".format(new_prefix))

        # Switch directories and create .pybombs
        cwd = os.getcwd()
        os.chdir(new_prefix)

        if os.path.isdir(".pybombs"):
            self.log.error("Prefix already exists in {}".format(new_prefix))
            return

        # Create the pybombs prefix
        # Eventually, it might be better to write this using a yaml parser rather than hard coding
        os.mkdir(".pybombs")
        config = open('.pybombs/config.yml', 'w')
        config.write("---\n")
        config.write("env:\n")
        config.write("  path: \"$PATH:$GRPREFIX/bin\"\n")
        config.write("  ld_load_library: \"$LD_LOAD_LIBRARY:$GRPREFIX/lib\"\n")
        config.write("  ld_library_path: \"$LD_LIBRARY_PATH:$GRPREFIX/lib\"\n")
        config.write("  pythonpath: \"$PYTHONPATH:$GRPREFIX/lib/python2.7/dist-packages\"\n")
        config.write("  pkg_config_path: \"$PKG_CONFIG_PATH:$GRPREFIX/lib/pkgconfig\"\n")
        config.write("  grc_blocks_path: \"$GRC_BLOCKS_PATH:$GRPREFIX/share/gnuradio/grc/blocks\"\n")
        config.close()

        #inventory = open('.pybombs/inventory.yml', 'w+')
        #inventory.close()

        # Switch back
        os.chdir(cwd)
