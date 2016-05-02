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
""" PyBOMBS command: Help """

import argparse
from pybombs.commands import CommandBase
from pybombs.config_manager import config_manager

class Help(CommandBase):
    """ Secret dairy component of PyBOMBS """
    cmds = {
        'help': 'Help',
    }

    def __init__(self, cmd, args):
        CommandBase.__init__(self,
                cmd, args,
                load_recipes=False,
                require_prefix=False,
        )

    @staticmethod
    def setup_subparser(parser, cmd=None):
        """
        Set up a subparser for 'help'
        """
        group = parser.add_argument_group("Help")
        group.add_argument(
                'help',
                action='append',
                default=None,
                nargs='?',
        )

    def run(self):
        """ Find help and print it """
        help_on = self.args.help[0]
        if help_on is None:
            config_manager.parser.print_help()
            return
        from pybombs.commands.base import init_arg_parser
        init_arg_parser(help_on)


