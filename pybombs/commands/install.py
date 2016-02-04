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
                exit(1)
        self.update_if_exists = (cmd == 'update' or self.args.update)
        self.fail_if_not_exists = (cmd == 'update')
        if get_all_pkgs:
            self.args.packages = self.inventory.get_packages()
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
        if len(install_tree) == 0 and not hasattr(self.args, 'quiet_install'):
            self.log.info("No packages to install.")
            return 0
        self.log.debug("Install tree:")
        if self.log.getEffectiveLevel() <= 20 or self.args.print_tree:
            install_tree.pretty_print()
        ### Recursively install/update, starting at the leaf nodes
        install_cache = []
        while len(install_tree):
            pkg = install_tree.pop_leaf_node()
            if pkg in install_cache:
                continue
            install_cache.append(pkg)
            if self.cmd == 'install' and self.args.deps_only and pkg in self.args.packages:
                self.log.debug("Skipping `{0}' because only deps are requested.")
                continue
            if self.pm.installed(pkg):
                self.log.info("Updating package: {0}".format(pkg))
                if not self.pm.update(pkg, verify=self.args.verify):
                    self.log.error("Error updating package {0}. Aborting.".format(pkg))
                    exit(1)
                self.log.info("Update successful.")
            else:
                self.log.info("Installing package: {0}".format(pkg))
                if not self.pm.install(pkg, static=self.args.static, verify=self.args.verify):
                    self.log.error("Error installing package {0}. Aborting.".format(pkg))
                    exit(1)
                self.log.info("Installation successful.")

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
        )

    def run(self):
        """ Moo, Moo, Moo! """
        print(r"         (__)    ")
        print(r"         (oo)    ")
        print(r"   /------\/     ")
        print(r"  / |    ||      ")
        print(r" *  /\---/\      ")
        print(r"    ~~   ~~      ")
        print(r"....\"Have you mooed today?\"...")

