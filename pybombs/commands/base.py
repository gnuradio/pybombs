#
# Copyright 2015-2016 Free Software Foundation, Inc.
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

import argparse
from six import iteritems

from pybombs import pb_logging
from pybombs.config_manager import config_manager
from pybombs.pb_exception import PBException

class CommandBase(object):
    """
    Base class for all PyBOMBS commands classes.
    All PyBOMBS command classes must derive from this.
    """
    cmds = {} # Add a key for every command; the value is the help string.
    hidden = False # Set to True if you don't want the command to show up in the help
    def __init__(self,
            cmd, args,
            load_recipes=False,
            require_prefix=True,
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
        self.prefix = None
        if self.cfg.get_active_prefix().prefix_dir is not None:
            self.prefix = self.cfg.get_active_prefix()
        elif require_prefix:
            self.log.error("No prefix specified. Aborting.")
            raise PBException("No prefix specified.")
        if self.prefix is not None:
            self.inventory = self.prefix.inventory

    @staticmethod
    def setup_subparser(parser, cmd=None):
        """
        Set up a subparser for a specific command
        """
        pass

    def run(self):
        """ Override this. """
        raise PBException("run() method not implemented for command {1}!".format(self.cmd))


class SubCommandBase(CommandBase):
    """
    Supplies methods if the command only consists of other subcommands
    """
    # Every entry: {'cmd': COMMAND, 'help': HELP_STR, 'subparser': SUBPARSER_CALLBACK, 'run': RUN_CALLBACK}
    subcommands = []

    def __init__(self,
            cmd, args,
            load_recipes=False,
            require_prefix=True,
        ):
        CommandBase.__init__(self, cmd, args, load_recipes, require_prefix)

    @staticmethod
    def setup_subcommandparser(parser, help_title, subcommands):
        """
        Set up a subparser for a specific subommand
        """
        subparsers = parser.add_subparsers(
                help=help_title,
                dest='sub_command',
        )
        for cmd, cmd_info in iteritems(subcommands):
            subparser = subparsers.add_parser(cmd, help=cmd_info['help'])
            if cmd_info['subparser'] is None:
                continue
            if isinstance(cmd_info['subparser'], tuple) or isinstance(cmd_info['subparser'], list):
                pass
                #for args in cmd_info['subparser']:
                    #subparser.add_argument(**args)
            else:
                cmd_info['subparser'](subparser)
        return parser

    def run(self):
        """ Go, go, go! """
        try:
            return self.subcommands[self.args.sub_command]['run'](self)()
        except KeyError:
            self.log.error("Illegal recipes command: {}".format(self.args.sub_command))
            return -1

##############################################################################
# Argument Parser
##############################################################################
def init_arg_parser(show_help_for=None, hide_hidden=True):
    """
    Create a base argument parser
    """
    def dummy_error(msg):
        raise PBException('parse error')
    cmd_list = get_cmd_list(hide_hidden=hide_hidden)
    # Set up global options:
    parser = argparse.ArgumentParser(
        description='PyBOMBS: A meta-package manager integrated with CGRAN.',
        epilog='Run `pybombs <command> --help to learn about command-specific options.',
    )
    config_manager.setup_parser(parser)
    subparsers = parser.add_subparsers(
        title='PyBOMBS subcommands',
        #description='valid subcommands',
        help="Description:",
        dest='command',
        metavar='<command>',
    )
    if hide_hidden:
        parser.error = dummy_error
    # Set up options for each command:
    for cmd in cmd_list:
        for cmd_name, cmd_help in iteritems(cmd.cmds):
            subparser = subparsers.add_parser(cmd_name, help=cmd_help, add_help=True)
            cmd.setup_subparser(subparser, cmd_name)
            if cmd_name == show_help_for:
                subparser.print_help()
                exit(0)
    return parser

##############################################################################
# Dispatcher functions
##############################################################################
def get_cmd_list(hide_hidden=False):
    """
    Returns a list of all command classes, excluding PyBombsCmd
    """
    from pybombs import commands
    cmd_list = []
    for g in commands.__dict__.values():
        try:
            if issubclass(g, CommandBase) and len(g.cmds) and not (hide_hidden and g.hidden):
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
        for cmd_name in cmd.cmds:
            cmd_dict[cmd_name] = cmd
    return cmd_dict

def dispatch():
    """
    Dispatch the actual command class
    """
    try:
        args = init_arg_parser().parse_args()
    except PBException:
        args = init_arg_parser(hide_hidden=False).parse_args()
    cmd_list = get_cmd_list()
    return get_cmd_dict(cmd_list)[args.command](cmd=args.command, args=args).run()

