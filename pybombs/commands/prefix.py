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
""" PyBOMBS command: prefix """

import pprint
from pybombs.commands import PyBombsCmd

class PyBombsPrefix(PyBombsCmd):
    """ Prefix operations """
    cmds = {
        'prefix': 'pkg stuff', # TODO nicer
    }

    @staticmethod
    def setup_subparser(parser, cmd=None):
        """
        Set up a subparser for a specific command
        """
        return parser

    def __init__(self, cmd, args):
        PyBombsCmd.__init__(self,
                cmd, args,
                load_recipes=True,
                require_prefix=True,
                require_inventory=True
        )

    def run(self):
        """ Go, go, go! """
        self.log.info('Prefix dir: {}'.format(self.prefix.prefix_dir))
        print 'Prefix env:'
        pprint.pprint(self.prefix.env)


