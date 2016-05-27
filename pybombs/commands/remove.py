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
""" PyBOMBS command: remove """

from __future__ import print_function
from pybombs.commands import CommandBase
from pybombs import package_manager
from pybombs import recipe
from pybombs import dep_manager
from pybombs.pb_exception import PBException

class Remove(CommandBase):
    """ Remove a package from this prefix """
    cmds = {
        'remove': 'Remove listed packages',
    }

    @staticmethod
    def setup_subparser(parser, cmd=None):
        """
        Set up a subparser for 'remove'
        """
        parser.add_argument(
                'packages',
                help="List of packages to remove",
                action='append',
                default=[],
                nargs='*'
        )
        parser.add_argument(
                '-d', '--no-deps',
                help="Do not remove dependees. May leave prefix in unusable state.",
                action='store_true',
        )

    def __init__(self, cmd, args):
        CommandBase.__init__(self,
                cmd, args,
                load_recipes=False,
                require_prefix=True,
        )
        self.args.packages = args.packages[0]
        if len(self.args.packages) == 0:
            self.log.error("No packages specified.")
            raise PBException("No packages specified.")
        # Do not allow any non-source packagers for this:
        self.cfg.set('packagers', '')
        self.pm = package_manager.PackageManager()
        if not self.args.no_deps:
            self.args.packages = self.get_dependees(self.args.packages)
            print(self.args.packages)

    def is_installed(self, pkg):
        """
        Returns True if pkg is either declared as installed by the package
        manager, or the the source package state is at least 'fetched'.
        """
        if self.pm.installed(pkg):
            return True
        if hasattr(self, 'inventory') \
                and self.inventory.get_state(pkg) is not None \
                and self.inventory.get_state(pkg) >= self.inventory.STATE_FETCHED:
            return True
        return False

    def run(self):
        """ Go, go, go! """
        ### Sanity checks
        for pkg in self.args.packages:
            if not self.is_installed(pkg):
                self.log.error("Package {0} is not installed. Aborting.".format(pkg))
                return 1
        dep_tree = dep_manager.DepManager().make_dep_tree(
            self.args.packages,
            lambda x: bool(x in self.args.packages),
        )
        ### Remove packages
        for pkg in reversed(dep_tree.serialize()):
            self.log.info("Removing package {0}.".format(pkg))
            # Uninstall:
            self.log.debug("Uninstalling.")
            if not self.pm.uninstall(pkg):
                self.log.warn("Could not uninstall {0} from prefix.".format(pkg))
            # Remove entry from inventory:
            self.log.debug("Removing package from inventory.")
            self.inventory.remove(pkg)
            self.inventory.save()

    def get_dependees(self, pkgs):
        """
        From a list of pkgs, return a list that also includes packages
        which depend on them.
        """
        self.log.debug("Resolving dependency list for clean removal.")
        other_installed_pkgs = [x for x in self.inventory.get_packages() if not x in pkgs]
        new_pkgs = []
        for other_installed_pkg in other_installed_pkgs:
            self.log.obnoxious("Checking if {0} is a dependee...".format(other_installed_pkg))
            try:
                deps = recipe.get_recipe(other_installed_pkg).depends or []
            except PBException:
                continue
            for pkg in pkgs:
                if pkg in deps:
                    self.log.obnoxious("Yup, it is.")
                    new_pkgs.append(other_installed_pkg)
                    break
        if len(new_pkgs) > 0:
            pkgs = pkgs + new_pkgs
            return self.get_dependees(pkgs)
        return pkgs

