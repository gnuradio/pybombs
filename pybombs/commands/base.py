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
""" Base class for PyBOMBS commands """

import os
import re
import argparse
from pybombs import pb_logging
from pybombs import inventory
from pybombs.config_manager import config_manager
from pybombs.pb_exception import PBException

class CommandBase(object):
    """
    Base class for all PyBOMBS commands classes.
    All PyBOMBS command classes must derive from this.
    """
    cmds = {}
    hidden = False
    def __init__(self,
            cmd, args,
            load_recipes=False,
            require_prefix=True,
            require_inventory=True
        ):
        self.cmd = cmd
        self.args = args
        self.log = pb_logging.logger.getChild(cmd)
        self.log.debug("Initializing command class for command {}".format(cmd))
        self.cfg = config_manager
        if not cmd in self.cmds.keys():
            raise PBException("{} is not a valid name for this command.".format(cmd))
        if load_recipes:
            from pybombs import recipe_manager
            self.recipe_manager = recipe_manager.recipe_manager
        if require_prefix:
            if self.cfg.get_active_prefix().prefix_dir is None:
                self.log.error("No prefix specified. Aborting.")
                exit(1)
            self.prefix = self.cfg.get_active_prefix()
        if require_inventory and require_prefix:
            self.inventory = inventory.Inventory(self.prefix.inv_file)
            self.inventory.load()

    @staticmethod
    def setup_subparser(self, parser, cmd=None):
        """
        Set up a subparser for a specific command
        """
        pass

    def run(self):
        """ Override this. """
        raise PBException("run() method not implemented for command {1}!".format(self._cmd))

##############################################################################
# Argument Parser
##############################################################################
def init_arg_parser(cmd_list):
    """
    Create a base argument parser
    """
    # Set up global options:
    parser = argparse.ArgumentParser(description='pybombs yo')
    config_manager.setup_parser(parser)
    subparsers = parser.add_subparsers(
            help="PyBOMBS Commands:",
            dest='command',
    )
    # Set up options for each command:
    cmd_name_list = []
    for cmd in cmd_list:
        for cmd_name, cmd_help in cmd.cmds.iteritems():
            subparser = subparsers.add_parser(cmd_name, help=cmd_help)
            cmd.setup_subparser(subparser, cmd_name)
            cmd_name_list.append(cmd_name)
    cmd_name_list.append('help')
    return parser

##############################################################################
# Dispatcher functions
##############################################################################
def get_cmd_list(the_globals):
    """
    Returns a list of all command classes, excluding PyBombsCmd
    """
    cmd_list = []
    for g in the_globals:
        try:
            if issubclass(g, CommandBase) and len(g.cmds):
                cmd_list.append(g)
        except (TypeError, AttributeError):
            pass
    return cmd_list

def get_cmd_dict(cmd_list):
    """
    Create a command: class type dict of all commands
    """
    cmd_dict = {}
    for cmd in cmd_list:
        for cmd_name in cmd.cmds.iterkeys():
            cmd_dict[cmd_name] = cmd
    return cmd_dict

def dispatch(the_globals):
    """
    Dispatch the actual command class
    """
    cmd_list = get_cmd_list(the_globals)
    parser = init_arg_parser(cmd_list)
    args = parser.parse_args()
    cmd_name = args.command
    cmd_obj = get_cmd_dict(cmd_list)[cmd_name](cmd=cmd_name, args=args)
    cmd_obj.run()
