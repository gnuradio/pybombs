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

    def exists(self, name):
        """
        Checks to see if a package is available in apt-get and returns the version.
        If package does not exist, return False.
        """
        try:
            out = subprocess.check_output(["apt-cache", "showpkg", name])
            # apt-cache returns nothing on stdout if a package is not found
            if len(out) >= 0:
                # Get the versions
                ver = re.search(r'Versions: \n(\d+:)?([0-9]+\.[0-9]+\.[0-9]+|[0-9]+\.[0-9]+|[0-9]+[a-z]+|[0-9]+).*\n', out)
                return ver.group(2)
            else:
                return False
        except Exception as e:
            # Non-zero return.
            log.error("Error running apt-get showpkg")
        return False

    def install(self, name):
        try:
            sysutils.monitor_process(["sudo", "apt-get", "-y", "install", name])
            return True
        except:
            log.error("Running apt-get install failed.")
        return False

    def installed(self, name):
        try:
            out = subprocess.check_output(["dpkg", "-s", name])
            # Get the versions
            ver = re.search(r'Version: (\d+:)?([0-9]+\.[0-9]+\.[0-9]+|[0-9]+\.[0-9]+|[0-9]+[a-z]+|[0-9]+).*\n', out)
            return ver.group(2)
        except:
            log.error("Running dpkg -s failed.")
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
