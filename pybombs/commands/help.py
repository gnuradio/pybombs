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

import sys
from pybombs.commands import *

def get_command_from_argv(possible_cmds):
    """ Read the requested command from argv. This can't be done with optparse,
    since the option parser isn't defined before the command is known, and
    optparse throws an error."""
    for arg in sys.argv:
        if arg[0] != "-" and arg in possible_cmds:
            return arg
    return None

def print_class_descriptions():
    """ Go through all PyBombs* classes and print their name,
        alias and description. """
    desclist = []
    for gvar in globals().values():
        try:
            if issubclass(gvar, CommandBase) \
                    and PyBombsHelp.cmds != gvar.cmds \
                    and not gvar.hidden:
                for cmd_name, cmd_help in gvar.cmds.iteritems():
                    desclist.append((cmd_name, cmd_help))
        except (TypeError, AttributeError):
            pass
    print '  Name       Description'
    print '======================================================'
    for description in desclist:
        print '  %-8s  %s' % description


class Help(CommandBase):
    """ Show some help. """
    cmds = {'help': 'Show help'}
    usage = """
    PyBOMBS -- The Python Build Overlay Management Build System.

    Module install tool for GNU Radio Out-Of-Tree Modules.

    Run pybombs help <COMMAND> to get some help on a specific command.
    """

    def __init__(self, cmd=None):
        CommandBase.__init__(self, cmd)

    def setup(self, options, args):
        " No setup necessary here. "
        pass

    def run(self):
        " Go, go, go! "
        cmd_dict = get_class_dict(globals().values())
        cmds = cmd_dict.keys()
        cmds.remove(self.cmds.keys()[0])
        help_requested_for = get_command_from_argv(cmds)
        if help_requested_for is None:
            print self.usage
            print '\nList of possible commands:\n'
            print_class_descriptions()
            return
        cmd_dict[help_requested_for]().setup_parser().print_help()
