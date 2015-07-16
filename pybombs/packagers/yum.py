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
Packager: yum
"""

import re
import subprocess
from pybombs.packagers.base import PackagerBase
from pybombs.utils import sysutils

class Yum(PackagerBase):
    """
    yum install xyz
    """
    name = 'yum'
    pkgtype = 'rpm'

    def __init__(self):
        PackagerBase.__init__(self)

    def supported(self):
        """
        Check if we can even run apt-get.
        Return True if so.
        """
        if sysutils.which('yum') is None:
            return False
        return True

    def _package_install(self, pkg_name, comparator=">=", required_version=None):
        """
        Call 'yum install pkgname' if we can satisfy the version requirements.
        """
        available_version = self.get_version_from_apt_cache(pkgname)
        if required_version is not None and not vcompare(comparator, required_version, available_version):
            return False
        try:
            sysutils.monitor_process(["sudo", "apt-get", "-y", "install", name])
            return True
        except:
            self.log.error("Running apt-get install failed.")
        return False

    def _package_installed(self, pkg_name, comparator=">=", required_version=None):
        """
        See if the installed version of pkgname matches the version requirements.
        """
        installed_version = self.get_version_from_dpkg(pkg_name)
        if not installed_version:
            return False
        if required_version is None:
            return True
        return vcompare(comparator, required_version, installed_version)

    def _package_exists(self, pkg_name, comparator=">=", required_version=None):
        """
        See if an installable version of pkgname matches the version requirements.
        """
        available_version = self.get_version_from_apt_cache(pkg_name)
        if required_version is not None and not vcompare(comparator, required_version, available_version):
            return False
        return available_version

    ### apt-get specific functions:
    def get_version_from_yum(self, pkgname):
        """
        Check which version is available in yum.
        """
        try:
            out = subprocess.check_output(["apt-cache", "showpkg", pkgname])
            # apt-cache returns nothing on stdout if a package is not found
            if len(out) >= 0:
                # Get the versions
                ver = re.search(
                        r'Versions: \n(?:\d+:)?(?P<ver>[0-9]+\.[0-9]+\.[0-9]+|[0-9]+\.[0-9]+|[0-9]+[a-z]+|[0-9]+).*\n',
                        out
                ).group('ver')
                self.log.debug("Package {} has version {} in apt-cache".format(pkgname, ver))
                return ver
            else:
                return False
        except Exception as e:
            # Non-zero return.
            self.log.error("Error running apt-get showpkg")
        return False

    #def get_version_from_dpkg(self, pkgname):
        #"""
        #Check which version is currently installed.
        #"""
        #try:
            ## dpkg -s will return non-zero if package does not exist, thus will throw
            #out = subprocess.check_output(["dpkg", "-s", pkgname])
            ## Get the versions
            ##ver = re.search(r'^Version: (?:\d+:)?([0-9]+\.[0-9]+\.[0-9]+|[0-9]+\.[0-9]+|[0-9]+[a-z]+|[0-9]+).*\n', out)
            #ver = re.search(r'^Version: (?:\d+:)?(?P<ver>.*)$', out, re.MULTILINE).group('ver')
            #self.log.debug("Package {} has version {} in dpkg".format(pkgname, ver))
            #return ver
        #except:
            #self.log.error("Running dpkg -s failed.")
        #return False


