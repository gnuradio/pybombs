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
""" PyBOMBS command: inv """

from __future__ import print_function
from pybombs.commands import CommandBase

class Inv(CommandBase):
    """ Remove a package from this prefix """
    cmds = {
        'inv': 'Query or update inventory',
    }

    @staticmethod
    def setup_subparser(parser, cmd=None):
        """
        Set up a subparser for 'config'
        """
        parser.add_argument(
            'pkg', nargs='?',
            help="Package for configuration key to query or set",
        )
        parser.add_argument(
            'value', nargs='?',
            help="New value",
        )
        parser.add_argument(
            '-k', '--key',
            help="Set or query this key instead of the install state",
        )

    def __init__(self, cmd, args):
        CommandBase.__init__(self,
            cmd, args,
            require_prefix=True,
        )
        verb = "Showing" if self.args.value is None else "Setting"
        if self.args.key is None:
            print("{verb} package state:".format(verb=verb))
        else:
            print("{verb} value for key `{key}':".format(verb=verb, key=self.args.key))

    def run(self):
        """ Go, go, go! """
        if self.args.pkg is None:
            return_value = 0
            for pkg in self.inventory.get_packages():
                self.args.pkg = pkg
                if self.run():
                    return_value = 1
            return return_value
        if not self.args.pkg in self.inventory.get_packages():
            self.log.error("`{0}' is not listed in inventory.".format(self.args.pkg))
            return 1
        print("{0}:\t".format(self.args.pkg), end='')
        if self.args.value is None:
            if self.args.key is None:
                print(self.inventory.get_state_name(self.inventory.get_state(self.args.pkg)))
            else:
                print(self.inventory.get_key(self.inventory.get_state(self.args.pkg), self.args.key))
        else:
            if self.args.key is None:
                self.inventory.set_state(self.args.pkg, self.args.value)
                print(self.inventory.get_state_name(self.inventory.get_state(self.args.pkg)))
            else:
                self.inventory.set_key(self.args.pkg, self.args.key, self.args.value)
                print(self.inventory.get_key(self.inventory.get_state(self.args.pkg), self.args.key))
            self.inventory.save()
        return 0

