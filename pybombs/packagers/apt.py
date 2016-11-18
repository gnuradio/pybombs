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
Packager: apt
"""

from __future__ import absolute_import
import re
import subprocess
from pybombs.packagers.extern import ExternCmdPackagerBase, ExternPackager
from pybombs.utils import subproc
from pybombs.utils import sysutils


class ExternalApt(ExternPackager):
    """
    Wrapper around apt(-get) and dpkg
    """
    def __init__(self, logger):
        ExternPackager.__init__(self, logger)
        # if sysutils.which('apt') is not None:
        if False: # To re-enable apt, replace this line with the one above (also need to change something further down)
            self.getcmd = 'apt'
            self.searchcmd = 'apt'
        else:
            self.getcmd = 'apt-get'
            self.searchcmd = 'apt-cache'

        try:
            import apt
            self.cache = apt.Cache()
        except (ImportError, AttributeError):
            # ImportError is caused by apt being completely missing
            # AttributeError is caused by us importing ourselves (we have no
            #   Cache() method) because python-apt is missing and we got a
            #   relative import instead
            self.log.info("Install python-apt to speed up apt processing.")
            self.cache = None

    def get_available_version(self, pkgname):
        """
        Check which version is available.
        """
        if self.cache:
            self.log.obnoxious("Checking apt for `{0}'".format(pkgname))
            (ver, is_installed) = self.check_cache(pkgname)
            if ver:
                self.log.debug("Package {0} has version {1} in repositories".format(pkgname, ver))
            return ver
        else:
            try:
                self.log.obnoxious("Checking {0} for `{1}'".format(self.searchcmd, pkgname))
                ver = subproc.match_output(
                    [self.searchcmd, "show", pkgname],
                    r'Version: (?:\d+:)?(?P<ver>[0-9]+\.[0-9]+\.[0-9]+|[0-9]+\.[0-9]+|[0-9]+[a-z]+|[0-9]+).*\n',
                    'ver'
                )
                if ver is None:
                    return False
                if ver:
                    self.log.debug("Package {0} has version {1} in repositories".format(pkgname, ver))
                return ver
            except subprocess.CalledProcessError:
                # Could be an issue, but most likely it means the package doesn't exist.
                self.log.debug(
                    "{cmd} show {pkg} failed.".format(cmd=self.searchcmd, pkg=pkgname)
                )
        return False

    def get_installed_version(self, pkgname):
        """
        Use dpkg (or python-apt) to determine and return the currently installed version.
        If pkgname is not installed, return None.
        """
        if self.cache:
            (ver, is_installed) = self.check_cache(pkgname)
            if is_installed:
                self.log.debug("Package {0} has version {1} installed".format(pkgname, ver))
            return ver if is_installed else False
        else:
            try:
                ver = subproc.match_output(
                    ["dpkg", "-s", pkgname],
                    r'^Version: (?:\d+:)?(?P<ver>[0-9]+\.[0-9]+\.[0-9]+|[0-9]+\.[0-9]+|[0-9]+[a-z]+|[0-9]+)',
                    'ver'
                )
                if ver is None:
                    self.log.debug("Looks like dpkg -s can't find package {pkg}. This is most likely a bug.".format(pkg=pkgname))
                    return False
                self.log.debug("Package {0} has version {1} installed".format(pkgname, ver))
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
        apt(-get) -y install pkgname
        """
        try:
            subproc.monitor_process([self.getcmd, "-y", "install", pkgname], elevate=True, throw=True)
            if self.cache:
                self.cache.open()
            return True
        except Exception as ex:
            self.log.error("Running {0} install failed.".format(self.getcmd))
            self.log.obnoxious(str(ex))
            return False

    def check_cache(self, pkgname):
        try:
            pkg = self.cache[pkgname]
        except:
            return (False, False)

        vers = pkg.versions
        first_ver = vers[0].version
        ver = re.search(r'(?:\d+:)?(?P<ver>[0-9]+\.[0-9]+\.[0-9]+|[0-9]+\.[0-9]+|[0-9]+[a-z]+|[0-9]+)', first_ver)
        if ver is None:
            return (False, pkg.is_installed)
        ver = ver.group('ver')
        return (ver, pkg.is_installed)



class Apt(ExternCmdPackagerBase):
    """
    apt(-get) install xyz
    """
    name = 'apt'
    pkgtype = 'deb'

    def __init__(self):
        ExternCmdPackagerBase.__init__(self)
        if self.supported():
            self.packager = ExternalApt(self.log)

    def supported(self):
        """
        Check if we're on a Debian/Ubuntu.
        Return True if so.
        """
        has_dpkg = sysutils.which('dpkg') is not None
        # has_apt = sysutils.which('apt') is not None or \
        # Replace this line with the one above to re-enable apt (also need to change something above):
        has_apt = False or \
            (sysutils.which('apt-cache') is not None \
            and sysutils.which('apt-get') is not None)
        return has_dpkg and has_apt

