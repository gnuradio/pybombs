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
import logging
from optparse import OptionParser, OptionGroup
#import recipe_loader
#import pb_logging

class PBException(BaseException):
    """ Standard exception for PyBOMBS commands. """
    pass

class PyBombsCmd(object):
    """
    Base class for all PyBOMBS commands classes.
    All PyBOMBS command classes must derive from this.
    """
    name = '__command__'
    hidden = False
    def __init__(self, load_recipes=False):
        self.parser = self.setup_parser()
        #if load_recipes:
            #recipe_loader.load_all()
        #self.log = pb_logging.logger
        # FIXME set logging level

    def get_usage_str(self):
        """ Returns a 'usage' string specific for this command. """
        return '%prog [GLOBAL FLAGS] {} [CMD FLAGS] <PATTERN>'.format(self.name)

    def setup_parser(self):
        """ Init the option parser. If derived classes need to add options,
        override this and call the parent function. """
        parser = OptionParser(add_help_option=False)
        parser.usage = self.get_usage_str()
        ogroup = OptionGroup(parser, "General options")
        ogroup.add_option("-v", "--verbose", default=False, action="count", help="Increase verbosity")
        ogroup.add_option("-c", "--continue", dest="_continue", default=False, action="store_true", help="Attempt to continue in-spite of failures")
        ogroup.add_option("-f", "--force", default=False, action="store_true", help="Force operation to occur")
        ogroup.add_option("-a", "--all", default=False, action="store_true", help="Apply operation to all packages if applicable")
        ogroup.add_option("-p", "--prefix", default=None, help="Specify a PyBOMBS prefix to use")
        ogroup.add_option("-r", "--recipes", default=None, help="Specify a directory containing recipes")
        opts, args = parser.parse_args()
        parser.add_option_group(ogroup)
        return parser

    def setup(self, options, args):
        """ Initialise all internal variables, such as the module name etc. """
        pass

    def run(self):
        """ Override this. """
        raise PBException("run() method not implemented for command {0}!".format(self.name))


def get_class_dict(the_globals):
    " Return a dictionary of the available commands in the form command->class "
    classdict = {}
    for g in the_globals:
        try:
            if issubclass(g, PyBombsCmd) and g.name != PyBombsCmd.name:
                classdict[g.name] = g
        except (TypeError, AttributeError):
            pass
    return classdict

