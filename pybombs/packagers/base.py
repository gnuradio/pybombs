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
        raise NotImplementedError()

    def installed(self, recipe):
        """
        Returns the installed version of package (identified by recipe)
        as a string, or False if the package is not installed.
        May also return True if a version can't be determined, but the
        recipe is installed.
        """
        raise NotImplementedError()

    def install(self, recipe, static=False):
        """
        Run the installation process for a package given a recipe.
        May raise an exception if things go terribly wrong.
        Otherwise, return True on success and False if installing
        failed in a controlled manner (e.g. the package wasn't available
        by this package manager).
        """
        raise NotImplementedError()

    def update(self, recipe):
        """
        Returns the updated version of package (identified by recipe)
        as a string, or False if the package is not installed.
        May also return True if a version can't be determined, but the
        recipe is installed.
        """
        raise NotImplementedError()

    def verify(self, recipe):
        """
        Returns the updated version of package (identified by recipe)
        as a string, or False if the package is not installed.
        May also return True if a version can't be determined, but the
        recipe is installed.
        """
        raise NotImplementedError()

    def uninstall(self, recipe):
        """
        Uninstalls the package (identified by recipe).

        Return True on Success or False on failure.
        """
        raise NotImplementedError()

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

