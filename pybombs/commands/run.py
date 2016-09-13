#
# Copyright 2016 Free Software Foundation, Inc.
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
""" PyBOMBS command: run """

from __future__ import print_function
import subprocess
from pybombs.commands import CommandBase

class Run(CommandBase):
    """ Run a command within a PyBOMBS context """
    cmds = {
        'run': 'Run a command within a PyBOMBS context',
    }

    @staticmethod
    def setup_subparser(parser, cmd=None):
        """
        Set up a subparser for 'config'
        """
        parser.add_argument(
            'cmd', nargs='+',
            help="Command to run in the prefix environment",
        )

    def __init__(self, cmd, args):
        CommandBase.__init__(self, cmd, args, require_prefix=True)

    def run(self):
        " Go, go, go! "
        cmd_env = self.cfg.get_active_prefix().env
        return subprocess.call(self.args.cmd, env=cmd_env)
