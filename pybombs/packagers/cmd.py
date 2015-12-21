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
Pseudo-Packager: Test command
"""

import re
import subprocess
from pybombs.packagers.base import PackagerBase
from pybombs.utils.vcompare import vcompare

class TestCommand(PackagerBase):
    """
    Try querying a tool by runnning a command.
    Can't really install stuff, but is useful for
    finding out if something is already installed.
    """
    name = 'cmd'
    pkgtype = 'cmd'

    def __init__(self):
        PackagerBase.__init__(self)

    def supported(self):
        """
        Always works
        """
        return True

    def _package_exists(self, pkgname, comparator=">=", required_version=None):
        """
        Existence and install-state of package is the same, so forward this.
        """
        return self._package_installed(pkgname, comparator, required_version)

    def _package_installed(self, pkgname, comparator=">=", required_version=None):
        """
        See if the installed version of pkgname matches version requirements.
        """
        installed_version = self.get_version_from_command(pkgname)
        if not installed_version:
            return False
        if required_version is None:
            return True
        if installed_version is True:
            return False
        if vcompare(comparator, installed_version, required_version):
            self.log.debug("Package {pkg} found via command line.".format(pkg=pkgname))
            return True
        return False

    def _package_install(self, pkgname, comparator=">=", required_version=None):
        """
        Can't install stuff, so this must always fail
        """
        return False

    def _package_update(self, pkgname, comparator=">=", required_version=None):
        """
        Can't update stuff, so this must always fail
        """
        return False

    ### pkg-config specific functions:
    def get_version_from_command(self, command):
        """
        Run command, see if it works. If the output has a version number in
        x.y.z format, return that. If it doesn't, but the command ran, return
        True. If it fails, return False. ezpz.
        """
        try:
            # If this fails, it almost always throws.
            # NOTE: the split is to handle multi-argument commands. There's
            # cases where this is not intended, e.g. it won't handle argument
            # with spaces! But currently this is preferable to running the
            # command in a shell, which would allow arbitrary commands.
            output = subprocess.check_output(command.split(), stderr=subprocess.STDOUT).strip()
            ver = re.search(
                r'(?P<ver>[0-9]+\.[0-9]+\.[0-9]+)',
                output,
                re.MULTILINE
            )
            if ver is None:
                self.log.debug("Could run, but couldn't find a version number.")
                return True
            ver = ver.group('ver')
            self.log.debug("Found version number: {0}".format(ver))
            return ver
        except (subprocess.CalledProcessError, OSError):
            # We'll assume it's not installed
            return False
        except Exception as e:
            self.log.error("Running `pkg-config --modversion` failed.")
            self.log.obnoxious(str(e))
        return False

