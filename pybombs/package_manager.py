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
"""
Package Manager: Manages packages (no shit)
"""

from pybombs import pb_logging
from pybombs.pb_exception import PBException
from pybombs.config_manager import config_manager
from pybombs import recipe
from pybombs import packagers
from pybombs.utils import vcompare

class PackageManager(object):
    """
    Meta-package manager. This will determine, according to our system
    and the configuration, who takes care of managing packages and
    then dispatches specific package managers. For example, this might
    dispatch an apt-get backend on Ubuntu and Debian systems, or a
    yum backend on Fedora systems.
    """
    def __init__(self,):
        # Set up logger:
        self.log = pb_logging.logger.getChild("PackageManager")
        self.cfg = config_manager
        self.prefix_available = self.cfg.get_active_prefix().prefix_dir is not None
        # Create a source package manager
        if self.prefix_available:
            self.src = packagers.Source()
            self.prefix = self.cfg.get_active_prefix()
        else:
            self.log.debug("No prefix specified. Skipping source package manager.")
        # Create sorted list of binary package managers
        requested_packagers = [x.strip() for x in self.cfg.get('packagers').split(',')]
        binary_pkgrs = []
        for pkgr in requested_packagers:
            self.log.debug("Attempting to add binary package manager {}".format(pkgr))
            p = packagers.get_by_name(pkgr, packagers.__dict__.values())
            if p is None:
                self.log.warn("This binary package manager can't be instantiated: {}".format(pkgr))
                continue
            if p.supported():
                self.log.debug("{} is supported!".format(pkgr))
                binary_pkgrs.append(p)
        self._packagers = []
        for satisfy in self.cfg.get('satisfy_order').split(','):
            satisfy = satisfy.strip()
            if satisfy == 'src':
                if self.prefix_available:
                    self._packagers += [self.src,]
            elif satisfy == 'native':
                self._packagers += binary_pkgrs
            else:
                raise PBException("Invalid satisfy_order value: {}".format(satisfy))
        self.log.debug("Using packagers: {}".format([x.name for x in self._packagers]))
        # Now we can use self.packagers, in order, for our commands.

    def check_package_flag(self, pkgname, flag, r=None):
        """
        See if package 'pkgname' has 'flag' set.
        """
        return self.cfg.get_package_flags(pkgname).has_key(flag) or \
                self.cfg.get_package_flags(pkgname, 'categories').has_key(flag)

    def get_packagers(self, pkgname):
        """
        Return a valid list of packagers for a given package.
        This will take care of cases where e.g. a source packager is
        required (and then only return that).
        """
        # Check if the package flags aren't forcing a source build:
        if self.check_package_flag(pkgname, 'forcebuild'):
            if not self.prefix_available:
                self.log.error("Package {} requires source-build, but no prefix is specified. Aborting.")
                exit(1)
            return [self.src,]
        return self._packagers

    def exists(self, name):
        """
        Check to see if this package is available on this platform.
        Returns True or a version string if yes, False if not.
        """
        r = recipe.get_recipe(name)
        if self.check_package_flag(name, 'forceinstalled', r):
            return True
        for pkgr in self.get_packagers(name):
            pkg_version = pkgr.exists(r)
            if pkg_version is None or not pkg_version:
                continue
            return pkg_version
        return False

    def installed(self, name):
        """
        Check to see if this recipe is installed (identified by its name)

        If yes, it returns True or a version string.
        Otherwise, returns False.
        """
        self.log.debug("Checking if package {} is installed.".format(name))
        r = recipe.get_recipe(name)
        if self.check_package_flag(name, 'forceinstalled', r):
            self.log.debug("Package {} is forced to state 'installed'.".format(name))
            # TODO maybe we can figure out a version string
            return True
        for pkgr in self.get_packagers(name):
            pkg_version = pkgr.installed(r)
            if pkg_version is None or not pkg_version:
                continue
            else:
                return True
        return False

    def install(self, name):
        """
        Install the given package. Returns True if successful, False otherwise.
        """
        r = recipe.get_recipe(name)
        if self.check_package_flag(name, 'forceinstalled', r):
            self.log.debug("Package {} is assumed installed.".format(name))
            # TODO maybe we can figure out a version string
            return True
        for pkgr in self.get_packagers(name):
            try:
                install_result = pkgr.install(r)
            except PBException as e:
                self.log.error(
                    "Something went wrong while trying to install {} using {}: {}".format(
                        name, pkgr.name, str(e)
                    )
                )
                continue
            if install_result:
                return True
        return False

    def update(self, name):
        """
        Update the given package. Returns True if successful, False otherwise.
        """
        r = recipe.get_recipe(name)
        for pkgr in self.get_packagers(name):
            try:
                update_result = pkgr.update(r)
            except PBException as e:
                self.log.error(
                    "Something went wrong while trying to update {} using {}: {}".format(
                        name, pkgr.name, str(e)
                    )
                )
                continue
            if update_result:
                return True
        return False

# Some test code:
if __name__ == "__main__":
    config_manager.set('packagers', 'dummy')
    config_manager.set('satisfy_order', 'native')
    pm = PackageManager()
    print pm.exists('gcc')
    print pm.installed('gcc')
    print pm.install('gcc')
