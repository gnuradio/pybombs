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
Packager Module: Dummy Packager
"""

from pybombs.packagers.base import PackagerBase
from pybombs import pb_logging

class Dummy(PackagerBase):
    name = 'dummy'
    """
    This isn't really a packager, this is just a dummy load
    for testing functions that require packagers.
    """
    def __init__(self):
        PackagerBase.__init__(self)

    def supported(self):
        """ This is always supported """
        return True

    def exists(self, recipe):
        """
        We'll always return version 0.0 here.
        """
        self.log.info("Pretending that package {} exists.".format(recipe.id))
        return "0.0"

    def install(self, recipe, static=False):
        """
        Pseudo-install package
        """
        self.log.info("Pretending to install package {}.".format(recipe.id))
        return True

    def update(self, recipe):
        """
        Pseudo-update package
        """
        self.log.info("Pretending to update package {}.".format(recipe.id))
        return True

    def installed(self, recipe):
        """
        We always pretend the package is not yet installed
        """
        return False

