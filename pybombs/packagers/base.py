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
Packager: Base class
"""

from pybombs import pb_logging
from pybombs.config_manager import config_manager

class PackagerBase(object):
    """
    Base class for packagers.
    """
    name = None
    pkgtype = None

    def __init__(self):
        self.cfg = config_manager
        self.log = pb_logging.logger.getChild("Packager.{}".format(self.name))

    def supported(self):
        """
        Return true if this platform is detected, e.g. on Debian systems
        return true for the 'apt-get' packager but False for the 'yum' packager.
        """
        raise NotImplementedError()

    def exists(self, recipe):
        """
        Checks to see if a package is available in this packager
        and returns the version as a string. If no version can be determined,
        return True.
        If not available, return None.
        """
        # If we run this code, the assumption is that we're running a
        # package manager. The source manager will override this function.
        self.log.obnoxious("exists({})".format(recipe.id))
        return self._packager_run_tree(recipe, self._package_exists)

    def installed(self, recipe):
        """
        Returns the installed version of package (identified by recipe)
        as a string, or False if the package is not installed.
        May also return True if a version can't be determined, but the
        recipe is installed.
        """
        # If we run this code, the assumption is that we're running a
        # package manager. The source manager will override this function.
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
        # If we run this code, the assumption is that we're running a
        # package manager. The source manager will override this function.
        self.log.obnoxious("install({}, static={})".format(recipe.id, static))
        return self._packager_run_tree(recipe, self._package_install)

    def update(self, recipe):
        """
        Returns the updated version of package (identified by recipe)
        as a string, or False if the package is not installed.
        May also return True if a version can't be determined, but the
        recipe is installed.
        """
        # If we run this code, the assumption is that we're running a
        # package manager. The source manager will override this function.
        self.log.obnoxious("Checking if recipe {} is installed".format(recipe.id))
        return self._packager_run_tree(recipe, self._package_installed)

    def verify(self, recipe):
        """
        Returns the updated version of package (identified by recipe)
        as a string, or False if the package is not installed.
        May also return True if a version can't be determined, but the
        recipe is installed.
        """
        self.log.obnoxious("Skipping verification of recipe {0}".format(recipe.id))
        return True

    def uninstall(self, recipe):
        """
        Uninstalls the package (identified by recipe).

        Return True on Success or False on failure.
        """
        self.log.info("No uninstall method specified for package {0}.".format(recipe.id))

    ### Package-manager specific helpers ####################################
    # Most packagers will work with a system packager in the background (e.g.
    # ap-get, dnf, etc. All of these pretty much have the same behaviour, and
    # only need the backend communication implemented.
    #
    # The source packager is the only exception, and will override the functions
    # above, orphaning these methods. But who cares.
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
        self.log.obnoxious("Calling ev for recursive satisfier rule evaluation")
        return satisfy_rule.ev(satisfy_evaluator)

    def _package_exists(self, pkg_name, comparator=">=", required_version=None):
        """
        Check if `pkg_name` is installable through this packager.
        Return type same as 'exists()'.
        """
        raise NotImplementedError()

    def _package_update(self, pkg_name, comparator=">=", required_version=None):
        """
        Updates a specific package through the current package manager.
        This is typically called by update() to do the actual package
        update call.
        Return type same as 'update()'.
        """
        raise NotImplementedError()

    def _package_install(self, pkg_name, comparator=">=", required_version=None):
        """
        Installs a specific package through the current package manager.
        This is typically called by install() to do the actual package
        install call.
        Returns False if the version comparison fails.
        """
        raise NotImplementedError()

    def _package_installed(self, pkg_name, comparator=">=", required_version=None):
        """
        Queries the current package mananger to see if a package is installed.
        Return type same as 'installed()'.
        """
        raise NotImplementedError()
    #
    #########################################################################

def get_by_name(name, objs):
    """
    Return a package manager by its name field. Not meant to be
    called by the user.
    """
    for obj in objs:
        try:
            if issubclass(obj, PackagerBase) and obj.name == name:
                return obj()
        except (TypeError, AttributeError):
            pass
    return None

