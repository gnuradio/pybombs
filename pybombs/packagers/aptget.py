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
from pybombs.utils import sysutils

class AptGet(PackagerBase):
    name = 'apt-get'
    pkgtype = 'deb'

    def __init__(self):
        PackagerBase.__init__(self)

    def supported(self):
        """
        Check if we can even run apt-get.
        Return True if so.
        """
        if sysutils.which('dpkg') is None \
            or sysutils.which('apt-cache') is None \
            or sysutils.which('apt-get') is None:
            return False
        return True

    #def exists(self, recipe):
        #"""
        #Checks to see if a package is available in apt-get and returns the version.
        #If package does not exist, return False.
        #"""
        #return self.get_version_from_apt_cache(recipe.
        #try:
            #out = subprocess.check_output(["apt-cache", "showpkg", name])
            ## apt-cache returns nothing on stdout if a package is not found
            #if len(out) >= 0:
                ## Get the versions
                #ver = re.search(r'Versions: \n(\d+:)?([0-9]+\.[0-9]+\.[0-9]+|[0-9]+\.[0-9]+|[0-9]+[a-z]+|[0-9]+).*\n', out).group(2)
                #self.log.debug("Package {} has version {}".format(recipe.id, ver)
                #return ver
            #else:
                #return False
        #except Exception as e:
            ## Non-zero return.
            #self.log.error("Error running apt-get showpkg")
        #return False

    def _package_install(self, pkg_name, comparator=">=", required_version=None):
        """
        Call 'apt-get install pkgname' if we can satisfy the version requirements.
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

    ### apt-get specific functions:
    def get_version_from_apt_cache(self, pkgname):
        """
        Check which version is available in apt-cache.
        """
        try:
            out = subprocess.check_output(["apt-cache", "showpkg", pkgname])
            # apt-cache returns nothing on stdout if a package is not found
            if len(out) >= 0:
                # Get the versions
                ver = re.search(r'Versions: \n(\d+:)?([0-9]+\.[0-9]+\.[0-9]+|[0-9]+\.[0-9]+|[0-9]+[a-z]+|[0-9]+).*\n', out).group(2)
                self.log.debug("Package {} has version {} in apt-cache".format(recipe.id, ver))
                return ver
            else:
                return False
        except Exception as e:
            # Non-zero return.
            self.log.error("Error running apt-get showpkg")
        return False

    def get_version_from_dpkg(self, pkgname):
        """
        Check which version is currently installed.
        """
        try:
            # dpkg -s will return non-zero if package does not exist, thus will throw
            out = subprocess.check_output(["dpkg", "-s", pkgname])
            # Get the versions
            #ver = re.search(r'^Version: (?:\d+:)?([0-9]+\.[0-9]+\.[0-9]+|[0-9]+\.[0-9]+|[0-9]+[a-z]+|[0-9]+).*\n', out)
            ver = re.search(r'^Version: (?:\d+:)?(?P<ver>.*)$', out, re.MULTILINE).group('ver')
            self.log.debug("Package {} has version {} in dpkg".format(pkgname, ver))
            return ver
        except:
            self.log.error("Running dpkg -s failed.")
        return False

# Some test code:
if __name__ == "__main__":
    pkgr = AptGet()
    #print ubuntu.exists("gcc")
    #print ubuntu.installed("gcc")
    #print ubuntu.install("gcc")
    #print ubuntu.exists("test", throw_ex=False)
    #print ubuntu.installed("test", throw_ex=False)
    #print ubuntu.install("test", throw_ex=False)
    #print ubuntu.exists("test")
