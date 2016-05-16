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

class PackageManagerCache(object):
    " Remember what's installed and installable "
    def __init__(self):
        self.known_installable = set()
        self.known_installed = set()

package_manager_cache = PackageManagerCache()

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
        self.pmc = package_manager_cache
        self.prefix_available = self.cfg.get_active_prefix().prefix_dir is not None
        # Create a source package manager
        if self.prefix_available:
            self.src = packagers.Source()
            self.prefix = self.cfg.get_active_prefix()
        else:
            self.log.debug("No prefix specified. Skipping source package manager.")
            self.src = None
        # Create sorted list of binary package managers
        requested_packagers = [x.strip() for x in self.cfg.get('packagers').split(',') if x]
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

    def check_package_flag(self, pkgname, flag):
        """
        See if package 'pkgname' has 'flag' set (return the boolean value
        of that flag if yes, or None otherwise).
        """
        return bool(
            self.cfg.get_package_flags(
                pkgname,
                recipe.get_recipe(pkgname).category
            ).get(flag)
        )

    def get_packagers(self, pkgname):
        """
        Return a valid list of packagers for a given package.
        This will take care of cases where e.g. a source packager is
        required (and then only return that).
        """
        # Check if the package flags aren't forcing a source build:
        if self.check_package_flag(pkgname, 'forcebuild'):
            self.log.debug("Package {pkg} is requesting a source build.".format(pkg=pkgname))
            if self.src is not None:
                return [self.src,]
            else:
                return []
        return self._packagers

    def exists(self, name, return_pkgr_name=False):
        """
        Check to see if this package is available on this platform.
        Returns True or a version string if yes, False if not.
        """
        if not return_pkgr_name and name in self.pmc.known_installable:
            self.log.obnoxious("{0} is cached and known to be installable.".format(name))
            return True
        self.log.debug("Checking if package {} is installable.".format(name))
        if self.check_package_flag(name, 'forceinstalled'):
            self.log.debug("Package {} is forced to state 'installed'.".format(name))
            return ['force-installed'] if return_pkgr_name else True
        r = recipe.get_recipe(name)
        pkgrs = []
        for pkgr in self.get_packagers(name):
            pkg_version = pkgr.exists(r)
            if pkg_version is None or not pkg_version:
                continue
            else:
                self.pmc.known_installable.add(name)
                if return_pkgr_name:
                    pkgrs.append(pkgr.name)
                else:
                    return pkg_version
        if return_pkgr_name and len(pkgrs):
            return pkgrs
        return False

    def installed(self, name, return_pkgr_name=False):
        """
        Check to see if this recipe is installed (identified by its name).

        If not, return False. If yes, return value depends on return_pkgr_name
        and is either a list of packager name that installed it, or a version
        string (if the version string can't be determined, returns True instead).
        """
        if not return_pkgr_name and name in self.pmc.known_installed:
            self.log.obnoxious("{0} is cached and known to be installed.".format(name))
            return True
        self.log.debug("Checking if package {} is installed.".format(name))
        if self.check_package_flag(name, 'forceinstalled'):
            self.log.debug("Package {} is forced to state 'installed'.".format(name))
            # TODO maybe we can figure out a version string
            return ['force-installed'] if return_pkgr_name else True
        r = recipe.get_recipe(name)
        pkgrs = []
        for pkgr in self.get_packagers(name):
            pkg_version = pkgr.installed(r)
            if pkg_version is None or not pkg_version:
                continue
            else:
                self.pmc.known_installed.add(name)
                if return_pkgr_name:
                    pkgrs.append(pkgr.name)
                else:
                    return pkg_version
        if return_pkgr_name and len(pkgrs):
            return pkgrs
        return False

    def install(self, name, static=False, verify=False):
        """
        Install the given package. Returns True if successful, False otherwise.
        """
        self.log.debug("install({}, static={})".format(name, static))
        if self.check_package_flag(name, 'forceinstalled'):
            self.log.debug("Package {} is assumed installed.".format(name))
            # TODO maybe we can figure out a version string
            return True
        pkgrs = self.get_packagers(name)
        if len(pkgrs) == 0:
            self.log.error("Can't find any packagers to install {0}".format(name))
            raise PBException("No packager available for package {0}".format(name))
        if static:
            self.log.debug('Package will be built statically.')
            if not self.prefix_available:
                self.log.error('Static builds require source builds.')
                raise PBException('Static builds require source builds.')
            pkgrs = [self.src,]
        pkg_optional = self.check_package_flag(name, 'optional')
        install_result = self._std_package_operation(
            name,
            'install',
            pkgrs,
            verify=verify,
            static=static,
        )
        if not install_result and pkg_optional:
            self.log.warn("Optional package {0} failed to install.".format(name))
            return True
        return install_result

    def update(self, name, verify=False):
        """
        Update the given package. Returns True if successful, False otherwise.
        """
        return self._std_package_operation(
            name,
            'update',
            self.get_packagers(name),
            verify=verify,
        )

    def uninstall(self, name):
        """
        Uninstall the given package.
        Returns True if successful, False otherwise.
        """
        return self._std_package_operation(
            name,
            'uninstall',
            self.get_packagers(name),
        )

    def _std_package_operation(self, name, operation, pkgrs, verify=False, **kwargs):
        """
        Standard package operation: Try an operation on all packagers.
        """
        rec = recipe.get_recipe(name)
        for pkgr in pkgrs:
            self.log.debug("Using packager {}".format(pkgr.name))
            try:
                result = getattr(pkgr, operation)(rec, **kwargs)
                if result:
                    if verify and not pkgr.verify(rec):
                        self.log.warn("Package reported successful {0}, but verification failed.".format(operation))
                        continue
                    return True
            except PBException as ex:
                self.log.error(
                    "Something went wrong while trying to {} {} using {}: {}".format(
                        operation, name, pkgr.name, str(ex).strip()
                    )
                )
        return False

