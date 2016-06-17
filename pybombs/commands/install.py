# -*- coding: utf-8 -*-
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
""" PyBOMBS command: install """

from __future__ import print_function
from pybombs.commands import CommandBase
from pybombs import install_manager
from pybombs.pb_exception import PBException

class Install(CommandBase):
    """ Install or update a package """
    cmds = {
        'install': 'Install listed packages',
        'update': 'Update listed packages',
    }

    @staticmethod
    def setup_subparser(parser, cmd=None):
        """
        Set up a subparser for 'install'
        """
        group = parser.add_argument_group("Install arguments" if cmd == 'install' else "Update arguments")
        group.add_argument(
                'packages',
                help="List of packages to install/update",
                action='append',
                default=[],
                nargs='*',
                metavar='PACKAGES'
        )
        group.add_argument(
                '--print-tree',
                help="Print dependency tree",
                action='store_true',
        )
        group.add_argument(
                '--no-deps',
                help="Skip dependencies (may cause builds to fail!)",
                action='store_true',
        )
        group.add_argument(
                '--verify',
                help="Verify installs were successful",
                action='store_true',
        )
        if cmd == 'install':
            group.add_argument(
                    '--static',
                    help="Build package(s) statically (implies source build)",
                    action='store_true',
            )
            group.add_argument(
                    '--deps-only',
                    help="Only install the dependencies, not the requested packages",
                    action='store_true',
            )
            group.add_argument(
                    '-u', '--update',
                    help="If packages are already installed, update them instead.",
                    action='store_true',
            )
        elif cmd == 'update':
            group.add_argument(
                    '-a', '--all',
                    help="Update all packages installed to current prefix, including dependencies.",
                    action='store_true',
            )

    def __init__(self, cmd, args):
        CommandBase.__init__(self,
                cmd, args,
                load_recipes=True,
                require_prefix=False, # Not required for non-source builds
        )
        self.args.packages = args.packages[0]
        get_all_pkgs = False
        if len(self.args.packages) == 0:
            if cmd == 'update':
                get_all_pkgs = True
                if not self.args.all:
                    self.args.no_deps = True
            else:
                self.log.error("No packages specified.")
                raise PBException("No packages specified.")
        self.update_if_exists = (cmd == 'update' or self.args.update)
        self.fail_if_not_exists = (cmd == 'update')
        if get_all_pkgs:
            self.args.packages = self.inventory.get_packages()
        self.install_manager = install_manager.InstallManager()

    def run(self):
        """ Go, go, go! """
        self.install_manager.install(
                self.args.packages,
                mode=self.cmd,
                fail_if_not_exists=self.fail_if_not_exists,
                update_if_exists=self.update_if_exists,
                quiet=False,
                print_tree=self.args.print_tree,
                deps_only=getattr(self.args, 'deps_only', False),
                no_deps=self.args.no_deps,
                verify=self.args.verify,
                static=getattr(self.args, 'static', False),
        )

### Damn, you found it :)
class Doge(CommandBase):
    """ Secret woofy component of PyBOMBS """
    cmds = {
        'doge': 'Doge',
    }
    hidden = True

    def __init__(self, cmd, args):
        CommandBase.__init__(self,
                cmd, args,
                load_recipes=False,
                require_prefix=False,
        )

    def run(self):
        """ Woof, woof, woof! """
        print(r"         ▄              ▄     ")
        print(r"        ▌▒█           ▄▀▒▌    ")
        print(r"        ▌▒▒▀▄       ▄▀▒▒▒▐    ")
        print(r"       ▐▄▀▒▒▀▀▀▀▄▄▄▀▒▒▒▒▒▐    ")
        print(r"     ▄▄▀▒▒▒▒▒▒▒▒▒▒▒█▒▒▄█▒▐    ")
        print(r"   ▄▀▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▀██▀▒▌    ")
        print(r"  ▐▒▒▒▄▄▄▒▒▒▒▒▒▒▒▒▒▒▒▒▀▄▒▒▌   ")
        print(r"  ▌▒▒▐▄█▀▒▒▒▒▄▀█▄▒▒▒▒▒▒▒█▒▐   ")
        print(r" ▐▒▒▒▒▒▒▒▒▒▒▒▌██▀▒▒▒▒▒▒▒▒▀▄▌  ")
        print(r" ▌▒▀▄██▄▒▒▒▒▒▒▒▒▒▒▒░░░░▒▒▒▒▌  ")
        print(r" ▌▀▐▄█▄█▌▄▒▀▒▒▒▒▒▒░░░░░░▒▒▒▐  ")
        print(r"▐▒▀▐▀▐▀▒▒▄▄▒▄▒▒▒▒▒░░░░░░▒▒▒▒▌ ")
        print(r"▐▒▒▒▀▀▄▄▒▒▒▄▒▒▒▒▒▒░░░░░░▒▒▒▐  ")
        print(r" ▌▒▒▒▒▒▒▀▀▀▒▒▒▒▒▒▒▒░░░░▒▒▒▒▌  ")
        print(r" ▐▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▐   ")
        print(r"  ▀▄▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▄▒▒▒▒▌   ")
        print(r"    ▀▄▒▒▒▒▒▒▒▒▒▒▄▄▄▀▒▒▒▒▄▀    ")
        print(r"   ▐▀▒▀▄▄▄▄▄▄▀▀▀▒▒▒▒▒▄▄▀      ")
        print(r"  ▐▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▀▀         ")
        print(r"                              ")
        print(r" Such code. Many packages. Wow")
