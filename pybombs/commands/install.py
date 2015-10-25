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
""" PyBOMBS command: install """

from pybombs.commands import CommandBase
from pybombs import package_manager
from pybombs import dep_manager

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
        parser.add_argument(
                'packages',
                help="List of packages to install",
                action='append',
                default=[],
                nargs='*'
        )
        parser.add_argument(
                '--print-tree',
                help="Print dependency tree",
                action='store_true',
        )
        parser.add_argument(
                '--no-deps',
                help="Skip dependencies",
                action='store_true',
        )
        if cmd == 'install':
            parser.add_argument(
                    '--static',
                    help="Build package(s) statically (implies source build)",
                    action='store_true',
            )
            parser.add_argument(
                    '-u', '--update',
                    help="If packages are already installed, update them instead.",
                    action='store_true',
            )
        elif cmd == 'update':
            parser.add_argument(
                    '-a', '--all',
                    help="Update all packages installed to current prefix, including dependencies.",
                    action='store_true',
            )

    def __init__(self, cmd, args):
        CommandBase.__init__(self,
                cmd, args,
                load_recipes=True,
                require_prefix=True,
                require_inventory=True,
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
                exit(1)
        self.update_if_exists = (cmd == 'update' or self.args.update)
        self.fail_if_not_exists = (cmd == 'update')
        if get_all_pkgs:
            self.args.packages = self.get_all_prefix_packages()
        self.pm = package_manager.PackageManager()

    def _check_if_pkg_goes_into_tree(self, pkg):
        """
        Return True if pkg has a legitimate right to be in the tree.
        """
        if self.fail_if_not_exists:
            return bool(self.pm.installed(pkg))
        return self.update_if_exists or not self.pm.installed(pkg)

    def run(self):
        """ Go, go, go! """
        ### Sanity checks
        if self.fail_if_not_exists:
            for pkg in self.args.packages:
                if not self.pm.installed(pkg):
                    self.log.error("Package {0} is not installed. Aborting.".format(pkg))
                    exit(1)
        ### Make install tree
        install_tree = dep_manager.DepManager().make_dep_tree(
            self.args.packages,
            self._check_if_pkg_goes_into_tree if not self.args.no_deps else lambda x: bool(x in self.args.packages)
        )
        self.log.debug("Install tree:")
        if self.log.getEffectiveLevel() <= 20 or self.args.print_tree:
            install_tree.pretty_print()
        ### Recursively install/update, starting at the leaf nodes
        while not install_tree.empty():
            pkg = install_tree.pop_leaf_node()
            if self.pm.installed(pkg):
                self.log.info("Updating package: {0}".format(pkg))
                if not self.pm.update(pkg):
                    self.log.error("Error updating package {0}. Aborting.".format(pkg))
                    exit(1)
                self.log.info("Update successful.")
            else:
                self.log.info("Installing package: {0}".format(pkg))
                if not self.pm.install(pkg, static=self.args.static):
                    self.log.error("Error installing package {0}. Aborting.".format(pkg))
                    exit(1)
                self.log.info("Installation successful.")

    def get_all_prefix_packages(self):
        """
        Return a list of all package names that are installed into the
        current prefix.
        """
        return self.inventory.get_packages()

### Damn, you found it :)
class Moo(CommandBase):
    """ Secret dairy component of PyBOMBS """
    cmds = {
        'moo': 'MOoO',
    }
    hidden = True

    def __init__(self, cmd, args):
        CommandBase.__init__(self,
                cmd, args,
                load_recipes=False,
                require_prefix=False,
                require_inventory=False,
        )

    def run(self):
        """ Moo, Moo, Moo! """
        print("         (__)    ")
        print("         (oo)    ")
        print("   /------\/     ")
        print("  / |    ||      ")
        print(" *  /\---/\      ")
        print("    ~~   ~~      ")
        print("....\"Have you mooed today?\"...")
