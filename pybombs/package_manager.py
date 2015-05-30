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

import os
import operator
from distutils.version import StrictVersion

import pb_logging
from pb_exception import PBException
from pybombs.config_manager import config_manager
import packagers

operators = {'<=': operator.le, '==': operator.eq, '>=': operator.ge, '!=': operator.ne}
compare = lambda x, y, z: operators[z](StrictVersion(x), StrictVersion(y))

# TODO: All these methods need to check if the package has a force-source flag set
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
        # Set up a default packager to use.
        self.default = packagers.Dummy()

    # Combine these and just use function pointers?
    def exists(self, name, version=None):
        """ Check to see if this package exists """

        # See if the package exist
        pkg = self.default.exists(name)

        # For now, just assume that the comparitor is greater than.
        # Maybe throw an exception here rather than True/False?
        if version:
            return compare(pkg, version, '>=')
        else:
            return True
        return False

    def installed(self, name, version=None):
        """ Check to see if this package is installed """

        pkg = self.default.installed(name)

        # For now, just assume that the comparitor is greater than.
        # Maybe throw an exception here rather than True/False?
        if version is not None:
            return compare(pkg, version, '>=')
        else:
            return pkg
        return False

    def install(self, name):
        """
        Install the given package
        """
        pkg = self.default.install(name)

    def update(self, name):
        """
        Update the given package
        """
        pkg = self.default.install(name)

# This is what you want to use
# Do we need this here?
#package_manager = PackageManager()

# Some test code:
if __name__ == "__main__":
    #system_manager.detect()
    print system_manager.default
    print system_manager.exists('gcc')
    print system_manager.installed('gcc')
    print system_manager.install('gcc')
