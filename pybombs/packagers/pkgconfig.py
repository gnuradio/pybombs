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
Packager: pkg-config
"""

import re
import subprocess
from pybombs.packagers.base import PackagerBase
from pybombs.utils import sysutils
from pybombs.utils.vcompare import vcompare

class PkgConfig(PackagerBase):
    """
    Uses pkg-config. Can't really install stuff, but is useful for
    finding out if something is already installed.
    """
    name = 'pkgconfig'
    pkgtype = 'pkgconfig'

    def __init__(self):
        PackagerBase.__init__(self)

    def supported(self):
        """
        Check if we can even run 'pkg-config'. Return True if yes.
        """
        return sysutils.which('pkg-config') is not None

    def _package_exists(self, pkgname, comparator=">=", required_version=None):
        """
        Existence and install-state of package is the same, so forward this.
        """
        return self._package_installed(pkgname, comparator, required_version)

    def _package_installed(self, pkgname, comparator=">=", required_version=None):
        """
        See if the installed version of pkgname matches the version requirements.
        """
        installed_version = self.get_version_from_pkgconfig(pkgname)
        if not installed_version:
            return False
        if required_version is None or vcompare(comparator, installed_version, required_version):
            return True
            self.log.debug("Package {pkg} found by pkg-config.".format(pkg=pkgname))
        return False

    def _package_install(self, pkgname, comparator=">=", required_version=None):
        """
        pkg-config can't install stuff, so this must always fail
        """
        return False

    ### pkg-config specific functions:
    def get_version_from_pkgconfig(self, pkgname):
        """
        Check which version is currently installed.
        """
        try:
            # pkg-config will return non-zero if package does not exist, thus will throw
            ver = subprocess.check_output(["pkg-config", "--modversion", pkgname], stderr=subprocess.STDOUT).strip()
            self.log.debug("Package {1} has version {1} in pkg-config".format(pkgname, ver))
            return ver
        except subprocess.CalledProcessError:
            # This usually means the packet is not installed
            return False
        except Exception as e:
            self.log.error("Running `pkg-config --modversion` failed.")
            self.log.obnoxious(str(e))
        return False

