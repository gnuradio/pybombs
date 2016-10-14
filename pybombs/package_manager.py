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

PACKAGE_MANAGER_CACHE = PackageManagerCache()

def _get_valid_install_type(install_type):
    " The return value is a valid install type. "
    if install_type is None:
        return "any"
    assert install_type in ("any", "source", "binary")
    return install_type

class PackageManager(object):
    """
    Meta-package manager. This will determine, according to our system
    and the configuration, who takes care of managing packages and
    then dispatches specific package managers. For example, this might
    dispatch an apt backend on Ubuntu and Debian systems, or a
    yum/dnf backend on Fedora systems.
    """
    def __init__(self,):
        # Set up logger:
        self.log = pb_logging.logger.getChild("PackageManager")
        self.cfg = config_manager
        self.pmc = PACKAGE_MANAGER_CACHE
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
        self.binary_pkgrs = []
        for pkgr in requested_packagers:
            self.log.debug("Attempting to add binary package manager {0}".format(pkgr))
            p = packagers.get_by_name(pkgr, packagers.__dict__.values())
            if p is None:
                self.log.warn("This binary package manager can't be instantiated: {0}".format(pkgr))
                continue
            if p.supported():
                self.log.debug("{0} is supported!".format(pkgr))
                self.binary_pkgrs.append(p)
        self.log.debug("Using binary packagers: {0}".format(str([x.name for x in self.binary_pkgrs])))
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

    def get_packagers(self, pkgname, install_type=None):
        """
        Return a valid list of packagers for a given package.
        This will take care of cases where e.g. a source packager is
        required (and then only return that).
        """
        install_type = _get_valid_install_type(install_type)
        force_build = self.check_package_flag(pkgname, 'forcebuild')
        if force_build:
            self.log.debug("Package {pkg} is requesting a source build.".format(pkg=pkgname))
        if install_type == "source" or (install_type == "any" and force_build):
            return [self.src,]
        if install_type == "binary" or self.src is None:
            if force_build:
                self.log.debug("Returning no packagers -- package is requesting source build, but binary build is requested.")
                return []
            return self.binary_pkgrs
        # if install_type == "any":
        return [self.src,] + self.binary_pkgrs

    def exists(self, name, return_pkgr_name=False):
        """
        Check to see if this package is available on this platform.
        Returns True or a version string if yes, False if not.
        """
        if not return_pkgr_name and name in self.pmc.known_installable:
            self.log.obnoxious("{0} is cached and known to be installable.".format(name))
            return True
        self.log.debug("Checking if package {0} is installable...".format(name))
        if self.check_package_flag(name, 'forceinstalled'):
            self.log.debug("Package {0} is forced to state 'installed'.".format(name))
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
        self.log.debug("Package {0} is not installable.".format(name))
        return False

    def installed(self, name, return_pkgr_name=False, install_type=None):
        """
        Check to see if this recipe is installed (identified by its name).

        If not, return False. If yes, return value depends on return_pkgr_name
        and is either a list of packager name that installed it, or a version
        string (if the version string can't be determined, returns True instead).
        """
        install_type = _get_valid_install_type(install_type)
        if not return_pkgr_name and name in self.pmc.known_installed:
            self.log.obnoxious("{0} is cached and known to be installed.".format(name))
            return True
        self.log.debug("Checking if package {0} is installed...".format(name))
        if self.check_package_flag(name, 'forceinstalled'):
            self.log.debug("Package {0} is forced to state 'installed'.".format(name))
            # TODO maybe we can figure out a version string
            return ['force-installed'] if return_pkgr_name else True
        r = recipe.get_recipe(name)
        pkgrs = []
        for pkgr in self.get_packagers(name, install_type):
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
        self.log.debug("Package {0} is not installed.".format(name))
        return False

    def install(
            self,
            name,
            install_type=None,
            static=False,
            verify=False,
            fail_silently=False
        ):
        """
        Install the given package. Returns True if successful, False otherwise.
        - install_type: Either "binary", "source" or "any" (default).
        - static: If True, will require a source build.
                  The 'static' option is then set for the package
        - verify: If True, a verification test is run after installation
                  (e.g. run unit tests, exact behaviour depends on recipe)
        - fail_silently: If True, no error is produced when a package can't
                         be installed (will still return False though)
        """
        install_type = _get_valid_install_type(install_type)
        self.log.debug("install({0}, install_type={1}, static={2})".format(name, install_type, static))
        if self.check_package_flag(name, 'forceinstalled'):
            self.log.debug("Package {0} is assumed installed.".format(name))
            # TODO maybe we can figure out a version string
            return True
        if static and install_type == "binary":
            if not fail_silently:
                self.log.error('Binary packager for static build was requested.')
            return False
        if static and install_type == "any":
            install_type = "source"
        pkgrs = self.get_packagers(name, install_type)
        if len(pkgrs) == 0:
            if fail_silently:
                return False
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
            if install_type == "binary":
                return False
            self.log.warn("Optional package {0} failed to install. Will pretend as if it had worked.".format(name))
            return True
        return install_result

    def update(self, name, verify=False, install_type=None):
        """
        Update the given package. Returns True if successful, False otherwise.
        """
        return self._std_package_operation(
            name,
            'update',
            self.get_packagers(name, install_type),
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
            self.log.debug("Using packager {0}".format(pkgr.name))
            try:
                result = getattr(pkgr, operation)(rec, **kwargs)
                if result:
                    if verify and not pkgr.verify(rec):
                        self.log.warn("Package reported successful {0}, but verification failed.".format(operation))
                        continue
                    return True
            except PBException as ex:
                self.log.error(
                    "Something went wrong while trying to {0} {1} using {2}: {3}".format(
                        operation, name, pkgr.name, str(ex).strip()
                    )
                )
        return False

