#
# Copyright 2015-2016 Free Software Foundation, Inc.
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
Packager: Base class for external packagers
"""

from pybombs.packagers.base import PackagerBase
from pybombs.utils.vcompare import vcompare

class ExternPackager(object):
    """
    Base class for wrappers around external packagers.
    """
    def __init__(self, logger):
        self.log = logger

    def get_available_version(self, pkgname):
        """
        Return a version that we can install through this package manager.
        """
        raise NotImplementedError

    def get_installed_version(self, pkgname):
        """
        Return the currently installed version. If pkgname is not installed,
        return None.
        """
        raise NotImplementedError

    def install(self, pkgname):
        """
        Install pkgname using this packager.
        """
        raise NotImplementedError

    def update(self, pkgname):
        """
        Update pkgname using this packager.
        Defaults to calling install().
        """
        return self.install(pkgname)

class ExternReadOnlyPackager(ExternPackager):
    """
    Wraps a read-only packager, i.e. one that can't itself install packages
    but can find out what's installed.
    """
    def __init__(self, logger):
        ExternPackager.__init__(self, logger)

    def get_available_version(self, pkgname):
        """
        The only available version is the installed version.
        """
        return self.get_installed_version(pkgname)

    def install(self, pkgname):
        """
        Can't install, by definition.
        """
        return False

class ExternCmdPackagerBase(PackagerBase):
    """
    Base class for packagers that use external commands (e.g. apt-get, yum).

    Most packagers will work with a system packager in the background (e.g.
    ap-get, dnf, etc. All of these pretty much have the same behaviour, and
    only need the backend communication implemented.
    """
    def __init__(self):
        PackagerBase.__init__(self)
        self.packager = None

    ### API calls ###########################################################
    def exists(self, recipe):
        """
        Checks to see if a package is available in this packager
        and returns the version as a string. If no version can be determined,
        return True.
        If not available, return None.
        """
        self.log.obnoxious("exists({})".format(recipe.id))
        return self._packager_run_tree(recipe, self._package_exists)

    def installed(self, recipe):
        """
        Returns the installed version of package (identified by recipe)
        as a string, or False if the package is not installed.
        May also return True if a version can't be determined, but the
        recipe is installed.
        """
        self.log.obnoxious("Checking if recipe {} is installed".format(recipe.id))
        return self._packager_run_tree(recipe, self._package_installed)

    def install(self, recipe, static=False):
        """
        Run the installation process for a package given a recipe.
        May raise an exception if things go terribly wrong.
        Otherwise, return True on success and False if installing
        failed in a controlled manner (e.g. the package wasn't available
        by this package manager).
        """
        self.log.obnoxious("install({}, static={})".format(recipe.id, static))
        return self._packager_run_tree(recipe, self._package_install)

    def update(self, recipe):
        """
        Returns the updated version of package (identified by recipe)
        as a string, or False if the package is not installed.
        May also return True if a version can't be determined, but the
        recipe is installed.
        """
        self.log.obnoxious("Checking if recipe {} is installed".format(recipe.id))
        return self._packager_run_tree(recipe, self._package_installed)

    def verify(self, recipe):
        """
        We can't really verify, we just need to trust the packager.
        """
        self.log.obnoxious("Skipping verification of recipe {0}".format(recipe.id))
        return True

    def uninstall(self, recipe):
        """
        Uninstalls the package (identified by recipe).

        Return True on Success or False on failure.
        """
        self.log.info("No uninstall method specified for package {0}.".format(recipe.id))

    ### Packager access #####################################################
    def _packager_run_tree(self, recipe, satisfy_evaluator):
        """
        Recursively evaluate satisfy rules given in a recipe.
        """
        try:
            satisfy_rule = recipe.get_package_reqs(self.pkgtype)
        except KeyError:
            self.log.debug("No satisfy rule for package type {}".format(self.pkgtype))
            return False
        if satisfy_rule is None:
            return None
        if satisfy_rule is True:
            self.log.debug(
                "Package {0} has an always-true satisfier for packager {1}".format(
                    recipe.id,
                    self.pkgtype,
                )
            )
            return True
        self.log.obnoxious("Calling ev for recursive satisfier rule evaluation")
        return satisfy_rule.ev(satisfy_evaluator)

    def _package_exists(self, pkg_name, comparator=">=", required_version=None):
        """
        Check if `pkg_name` is installable through this packager.
        Return type same as 'exists()'.
        """
        available_version = self.packager.get_available_version(pkg_name)
        if available_version is True:
            return True
        if available_version is False \
                or (required_version is not None and not vcompare(comparator, available_version, required_version)):
            return False
        return available_version

    def _package_update(self, pkg_name, comparator=">=", required_version=None):
        """
        Updates a specific package through the current package manager.
        This is typically called by update() to do the actual package
        update call.
        Return type same as 'update()'.
        """
        if not self._package_exists(pkg_name, comparator, required_version):
            return False
        if not self.packager.update(pkg_name):
            return False
        installed_version = self.packager.get_installed_version(pkg_name)
        if installed_version is False \
                or (required_version is not None and not vcompare(comparator, installed_version, required_version)):
            return False
        return True


    def _package_install(self, pkg_name, comparator=">=", required_version=None):
        """
        Installs a specific package through the current package manager.
        This is typically called by install() to do the actual package
        install call.
        Returns False if the version comparison fails.
        """
        if not self._package_exists(pkg_name, comparator, required_version):
            return False
        if not self.packager.install(pkg_name):
            return False
        installed_version = self.packager.get_installed_version(pkg_name)
        if installed_version is False \
                or (required_version is not None and not vcompare(comparator, installed_version, required_version)):
            return False
        return True

    def _package_installed(self, pkg_name, comparator=">=", required_version=None):
        """
        Queries the current package mananger to see if a package is installed.
        Return type same as 'installed()'.
        """
        installed_version = self.packager.get_installed_version(pkg_name)
        if not installed_version:
            return False
        if required_version is None:
            return True
        try:
            return vcompare(comparator, installed_version, required_version)
        except TypeError:
            return False

