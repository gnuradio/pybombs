#!/usr/bin/env python
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
""" PyBOMBS command: recipes """

import pprint
from pybombs.commands import PyBombsCmd

class PyBombsRecipes(PyBombsCmd):
    """
    Manage recipe lists
    """
    cmds = {
        'recipes': 'Manage recipe lists',
    }
    location_types = ('dir', 'git', 'http')

    @staticmethod
    def setup_subparser(parser, cmd=None):
        """
        Set up a subparser for a specific command
        """
        subparsers = parser.add_subparsers(
                help="Prefix Commands:",
                dest='prefix_command',
        )
        recipes_cmd_name_list = {
            'add':    ('Add a new recipes location.', self.setup_subsubparser_add),
            'remove': ('Remove a recipes location.', self.setup_subsubparser_remove),
            'update': ('Update recipes with a remote repository', self.setup_subsubparser_update),
        }
        for cmd_name, cmd_info in recipes_cmd_name_list.iteritems():
            subparser = subparsers.add_parser(cmd_name, help=cmd_info[0])
            cmd_info[1](subparser)
        return parser

    @staticmethod
    def setup_subsubparser_add(parser):
        parser.add_parser(
            'url',
            help="Location of recipes (URL or directory)",
        )

    @staticmethod
    def setup_subsubparser_remove(parser):
        parser.add_parser(
            'alias',
            help="Name of recipe location to remove",
        )

    @staticmethod
    def setup_subsubparser_update(parser):
        parser.add_parser(
            'alias',
            help="Name of recipe location to update",
        )

    def __init__(self, cmd, args):
        PyBombsCmd.__init__(self,
                cmd, args,
                load_recipes=False,
                require_prefix=False,
                require_inventory=False
        )

    def run(self):
        """ Go, go, go! """
        if self.args.prefix_command == 'add':
            self._add_recipes()
        elif self.args.prefix_command == 'remove':
            self._remove_recipes()
        elif self.args.prefix_command == 'update':
            self._update_recipes()
        else:
            self.log.error("Illegal recipes command: {}".format(self.args.prefix_command))

    def _add_recipes(self):
        pass
        # - Check name is not yet taken
        # - Detect type
        # - git clone or http download

    def _remove_recipes(self):
        pass

    def _update_recipes(self):
        pass

