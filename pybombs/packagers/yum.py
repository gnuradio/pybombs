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
Packager: yum or dnf
"""

import re
import subprocess
from pybombs.packagers.base import PackagerBase
from pybombs.utils import subproc
from pybombs.utils import sysutils
from pybombs.utils.vcompare import vcompare

class YumDnf(PackagerBase):
    """
    yum/dnf install xyz
    """
    name = 'yumdnf'
    pkgtype = 'rpm'

    def __init__(self):
        PackagerBase.__init__(self)
        self.command = None
        if sysutils.which('dnf') is not None:
            self.command = 'dnf'
        elif sysutils.which('yum') is not None:
            self.command = 'yum'

    def supported(self):
        """
        Check if we can even run apt-get.
        Return True if so.
        """
        return self.command is not None

    def _package_exists(self, pkgname, comparator=">=", required_version=None):
        """
        See if an installable version of pkgname matches the version requirements.
        """
        available_version = self.get_available_version(pkgname)
        if available_version is False \
                or (required_version is not None and not vcompare(comparator, available_version, required_version)):
            return False
        return available_version

    def _package_installed(self, pkgname, comparator=">=", required_version=None):
        """
        See if the installed version of pkgname matches the version requirements.
        """
        installed_version = self.get_installed_version(pkgname)
        if not installed_version:
            return False
        if required_version is None:
            return True
        return vcompare(comparator, installed_version, required_version)

    def _package_install(self, pkgname, comparator=">=", required_version=None, cmd='install'):
        """
        Call 'COMMAND install pkgname' if we can satisfy the version requirements.
        """
        if not self._package_exists(pkgname, comparator, required_version):
            return False
        try:
            subproc.monitor_process([self.command, "-y", cmd, pkgname], elevate=True)
        except Exception as ex:
            self.log.error("Running `{0} install' failed.".format(self.command))
            self.log.obnoxious(str(ex))
            return False
        installed_version = self.get_installed_version(pkgname)
        if installed_version is False \
                or (required_version is not None and not vcompare(comparator, installed_version, required_version)):
            return False
        return True

    def _package_update(self, pkgname, comparator=">=", required_version=None):
        """
        Call 'COMMAND update pkgname' if we can satisfy the version requirements.
        """
        return self._package_install(pkgname, comparator, required_version, cmd='update')

    ### packager-specific functions:
    def get_available_version(self, pkgname):
        """
        Check which version is available in the packager.
        """
        try:
            out = subprocess.check_output([self.command, "info", pkgname]).strip()
            if len(out) == 0:
                self.log.debug("Did not expect empty output for `{0} info'...".format(self.command))
                return False
            ver = re.search(r'^Version\s+:\s+(?P<ver>.*$)', out, re.MULTILINE).group('ver')
            self.log.debug("Package {} has version {} in {}".format(pkgname, ver, self.command))
            return ver
        except subprocess.CalledProcessError as ex:
            # This usually means the package was not found, so don't worry
            self.log.obnoxious("`{0} info' returned non-zero exit status.".format(self.command))
            self.log.obnoxious(str(ex))
            return False
        except Exception as ex:
            self.log.error("Error parsing {0} info".format(self.command))
            self.log.error(str(ex))
        return False

    def get_installed_version(self, pkgname):
        """
        Check which version is currently installed.
        """
        try:
            # 'list installed' will return non-zero if package does not exist, thus will throw
            out = subprocess.check_output(
                    [self.command, "list", "installed", pkgname],
                    stderr=subprocess.STDOUT
            ).strip().split("\n")
            # Output looks like this:
            # <pkgname>.<arch>   <version>   <more info>
            # So, two steps:
            # 1) Check that pkgname is correct
            # 2) return version
            for line in out:
                mobj = re.match(r"^(?P<pkg>[^\.]+)\.(?P<arch>\S+)\s+(\d+:)?(?P<ver>[0-9]+(\.[0-9]+){0,2})", line)
                if mobj and mobj.group('pkg') == pkgname:
                    ver = mobj.group('ver')
                    self.log.debug("Package {} has version {} in {}".format(pkgname, ver, self.command))
                    return ver
            return False
        except subprocess.CalledProcessError:
            # This usually means the packet is not installed
            return False
        except Exception as ex:
            self.log.error("Parsing `{0} list installed` failed.".format(self.command))
            self.log.obnoxious(str(ex))
        return False
