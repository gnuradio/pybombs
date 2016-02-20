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
Packager: apt-get
"""

import re
import subprocess
from pybombs.packagers.base import PackagerBase
from pybombs.utils import subproc
from pybombs.utils import sysutils
from pybombs.utils.vcompare import vcompare

class AptGet(PackagerBase):
    """
    apt-get install xyz
    """
    name = 'apt-get'
    pkgtype = 'deb'

    def __init__(self):
        PackagerBase.__init__(self)

    def supported(self):
        """
        Check if we can even run apt-get.
        Return True if so.
        """
        return sysutils.which('dpkg') is not None \
            and sysutils.which('apt-cache') is not None \
            and sysutils.which('apt-get') is not None

    def _package_exists(self, pkg_name, comparator=">=", required_version=None):
        """
        See if an installable version of pkgname matches the version requirements.
        """
        available_version = self.get_version_from_apt_cache(pkg_name)
        if available_version is False \
                or (required_version is not None and not vcompare(comparator, available_version, required_version)):
            return False
        return available_version

    def _package_installed(self, pkg_name, comparator=">=", required_version=None):
        """
        See if the installed version of pkgname matches the version requirements.
        """
        installed_version = self.get_version_from_dpkg(pkg_name)
        if not installed_version:
            return False
        if required_version is None:
            return True
        return vcompare(comparator, installed_version, required_version)

    def _package_install(self, pkg_name, comparator=">=", required_version=None):
        """
        Call 'apt-get install pkgname' if we can satisfy the version requirements.
        """
        if not self._package_exists(pkg_name, comparator, required_version):
            return False
        try:
            subproc.monitor_process(["apt-get", "-y", "install", pkg_name], elevate=True)
        except Exception as ex:
            self.log.error("Running apt-get install failed.")
            self.log.obnoxious(str(ex))
            return False
        installed_version = self.get_version_from_dpkg(pkg_name)
        if installed_version is False \
                or (required_version is not None and not vcompare(comparator, installed_version, required_version)):
            return False
        return True

    def _package_update(self, pkg_name, comparator=">=", required_version=None):
        """
        Call 'apt-get install pkgname' if we can satisfy the version requirements.
        """
        return self._package_install(pkg_name, comparator, required_version)

    ### apt-get specific functions:
    def get_version_from_apt_cache(self, pkgname):
        """
        Check which version is available in apt-cache.
        """
        try:
            self.log.obnoxious("Checking apt-cache for `{0}'".format(pkgname))
            out = subprocess.check_output(["apt-cache", "showpkg", pkgname])
            # apt-cache returns nothing on stdout if a package is not found
            if len(out) >= 0:
                # Get the versions
                ver = re.search(
                    r'Versions: \n(?:\d+:)?(?P<ver>[0-9]+\.[0-9]+\.[0-9]+|[0-9]+\.[0-9]+|[0-9]+[a-z]+|[0-9]+).*\n',
                    out
                )
                if ver is None:
                    return False
                ver = ver.group('ver')
                self.log.debug("Package {} has version {} in apt-cache".format(pkgname, ver))
                return ver
            else:
                return False
        except subprocess.CalledProcessError:
            # Non-zero return. Shouldn't happen, even if package is not found.
            self.log.error("Error running apt-cache showpkg")
        return False

    def get_version_from_dpkg(self, pkgname):
        """
        Check which version is currently installed.
        """
        try:
            # dpkg -s will return non-zero if package does not exist, thus will throw
            out = subprocess.check_output(["dpkg", "-s", pkgname], stderr=subprocess.STDOUT)
            # Get the versions
            #ver = re.search(r'^Version: (?:\d+:)?([0-9]+\.[0-9]+\.[0-9]+|[0-9]+\.[0-9]+|[0-9]+[a-z]+|[0-9]+).*\n', out)
            ver = re.search(
                r'^Version: (?:\d+:)?(?P<ver>[0-9]+\.[0-9]+\.[0-9]+|[0-9]+\.[0-9]+|[0-9]+[a-z]+|[0-9]+)',
                out,
                re.MULTILINE
            )
            if ver is None:
                self.log.debug("Looks like dpkg -s can't find package {pkg}".format(pkg=pkgname))
                return False
            ver = ver.group('ver')
            self.log.debug("Package {} has version {} in dpkg".format(pkgname, ver))
            return ver
        except subprocess.CalledProcessError:
            # This usually means the packet is not installed -- not a problem.
            return False
        except Exception as e:
            self.log.error("Running dpkg -s failed.")
            self.log.obnoxious(str(e))
        return False
