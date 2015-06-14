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
    def __init__(self):
        self.cfg = config_manager
        self.log = pb_logging.logger.getChild("Packager.{}".format(self.name))

    def supported(self):
        """
        Return true if this platform is detected.
        """
        raise NotImplementedError()

    def exists(self, recipe):
        """
        Checks to see if a package is available in this packager
        and returns the version as a string.
        If not available, return None, or raise an exception if throw_ex
        is True.
        """
        raise NotImplementedError()

    def install(self, recipe):
        """
        Run the installation process for package 'name'.

        May raise an exception if things go terribly wrong.
        Otherwise, return True on success and False if installing
        failed in an expected manner (e.g. the package wasn't available
        by this package manager).
        """
        raise NotImplementedError()

    def installed(self, recipe):
        """
        Returns the version of package 'name' as a string, or
        False if the package is not installed. May also return
        True if a version can't be determined.
        """
        raise NotImplementedError()

def get_by_name(name):
    """
    Return a package manager by its name field. Not meant to be
    called by the user.
    """
    from pybombs.packagers import *
    for g in locals().values():
        try:
            if issubclass(g, PackagerBase) and g.name == name:
                return g()
        except (TypeError, AttributeError):
            pass
    return None

