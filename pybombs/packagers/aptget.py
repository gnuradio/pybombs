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
Packager: apt-get
"""

import subprocess
from pybombs.packagers.extern import ExternCmdPackagerBase, ExternPackager
from pybombs.utils import subproc
from pybombs.utils import sysutils

class ExternalAptGet(ExternPackager):
    """
    Wrapper around apt-get and dpkg
    """
    def __init__(self, logger):
        ExternPackager.__init__(self, logger)

    def get_available_version(self, pkgname):
        """
        Check which version is available in apt-cache.
        """
        try:
            self.log.obnoxious("Checking apt-cache for `{0}'".format(pkgname))
            ver = subproc.match_output(
                ["apt-cache", "showpkg", pkgname],
                r'Versions: \n(?:\d+:)?(?P<ver>[0-9]+\.[0-9]+\.[0-9]+|[0-9]+\.[0-9]+|[0-9]+[a-z]+|[0-9]+).*\n',
                'ver'
            )
            if ver is None:
                return False
            if ver:
                self.log.debug("Package {} has version {} in apt-cache".format(pkgname, ver))
            return ver
        except subprocess.CalledProcessError:
            self.log.error("Error running apt-cache showpkg. This shouldn't happen. Probably a bug.")
        return False

    def get_installed_version(self, pkgname):
        """
        Use dpkg to determine and return the currently installed version.
        If pkgname is not installed, return None.
        """
        try:
            ver = subproc.match_output(
                ["dpkg", "-s", pkgname],
                r'^Version: (?:\d+:)?(?P<ver>[0-9]+\.[0-9]+\.[0-9]+|[0-9]+\.[0-9]+|[0-9]+[a-z]+|[0-9]+)',
                'ver'
            )
            if ver is None:
                self.log.debug("Looks like dpkg -s can't find package {pkg}. This is most likely a bug.".format(pkg=pkgname))
                return False
            self.log.debug("Package {} has version {} in dpkg".format(pkgname, ver))
            return ver
        except subprocess.CalledProcessError:
            # This usually means the packet is not installed -- not a problem.
            return False
        except Exception as e:
            self.log.error("Running dpkg -s failed.")
            self.log.obnoxious(str(e))
        return False

    def install(self, pkgname):
        """
        apt-get -y install pkgname
        """
        try:
            subproc.monitor_process(["apt-get", "-y", "install", pkgname], elevate=True, throw=True)
            return True
        except Exception as ex:
            self.log.error("Running apt-get install failed.")
            self.log.obnoxious(str(ex))
            return False


class AptGet(ExternCmdPackagerBase):
    """
    apt-get install xyz
    """
    name = 'apt-get'
    pkgtype = 'deb'

    def __init__(self):
        ExternCmdPackagerBase.__init__(self)
        self.packager = ExternalAptGet(self.log)

    def supported(self):
        """
        Check if we can even run apt-get.
        Return True if so.
        """
        return sysutils.which('dpkg') is not None \
            and sysutils.which('apt-cache') is not None \
            and sysutils.which('apt-get') is not None

