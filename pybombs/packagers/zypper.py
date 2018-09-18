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
Packager: zypper (OpenSUSE)
"""

import os
import re
import subprocess
from pybombs.packagers.extern import ExternCmdPackagerBase, ExternPackager
from pybombs.utils import subproc
from pybombs.utils import sysutils
from pybombs.utils import utils

class ExternalZypper(ExternPackager):
    """
    Wrapper for zypper
    """
    def __init__(self, logger):
        ExternPackager.__init__(self, logger)
        self.command = None
        if sysutils.which('zypper') is not None:
            self.command = 'zypper'
        if sysutils.which('rpm') is not None:
            self.fastcommand = 'rpm'
        else:
            self.fastcommand = None

    def get_available_version(self, pkgname):
        """
        Return a version that we can install through this package manager.
        """
        try:
            ver = subproc.match_output(
                [self.command, "info", pkgname],
                r'^Version\s+:\s+(?P<ver>.*$)',
                'ver',
                 env=utils.dict_merge(os.environ, {'LC_ALL': 'C'}),
            )
            if ver is None:
                return False
            self.log.debug("Package {0} has version {1} in {2}".format(pkgname, ver, self.command))
            return ver
        except subproc.CalledProcessError as ex:
            # This usually means the package was not found, so don't worry
            self.log.trace("`{0} info' returned non-zero exit status.".format(self.command))
            self.log.trace(str(ex))
            return False
        except Exception as ex:
            self.log.error("Error parsing {0} info".format(self.command))
            self.log.error(str(ex))
        return False

    def get_installed_version(self, pkgname):
        """
        Return the currently installed version. If pkgname is not installed,
        return False.
        """
        pkgarch = None
        if pkgname.find('.') != -1:
            pkgname, pkgarch = pkgname.split('.', 1)
        # zypper is very slow for mere queries of installed packages,
        # if we have rpm do that
        if self.fastcommand is not None:
            try:
                # using RPM we can query just what we want, and much faster
                pkg, ver, arch = subproc.check_output(
                                   [self.fastcommand, "-q", 
                                    '--qf=%{NAME}\ %{VERSION}-%{RELEASE}\ %{ARCH}', 
                                    pkgname]).strip().split()
                if pkg == pkgname and (pkgarch is None or arch == pkgarch):
                    self.log.debug("Package {0} has version {1} in {2}".format(pkgname, ver, self.fastcommand))
                    return ver
            # exception for unpack error if package not found
            except subproc.CalledProcessError:
                pass
            except Exception as ex:
                self.log.error("Parsing `{0} list installed` failed.".format(self.fastcommand))
                self.log.trace(str(ex))
            return False
        try:
            # 'list installed' will return non-zero if package does not exist, thus will throw
            out = subproc.check_output(
                    [self.command, "search", "-is", pkgname],
                    stderr=subprocess.STDOUT
            ).strip().split("\n")
            # Output looks like this:
            # <status>|<pkgname>|<type>|<version>|<arch>|<repo>
            # So, two steps:
            # 1) Check that pkgname is correct (and, if necessary, the package arch)
            # 2) return version
            match_pat = r"^(?P<status>)\s+\|\s+(?P<pkg>[^\.]+)\s+\| \
                        \s+(?P<pkgtype>\S+)\s+\| \
                        \s+(?P<ver>[0-9]+([.-][0-9a-z]+))\s+\| \
                        \s+(?P<arch>\S+)\s+(\d+:)"
            matcher = re.compile(match_pat)
            for line in out:
                mobj = matcher.match(line)
                if mobj and mobj.group('pkg') == pkgname:
                    if pkgarch is not None and mobj.group('arch') != pkgarch:
                        continue
                    ver = mobj.group('ver')
                    self.log.debug("Package {0} has version {1} in {2}".format(pkgname, ver, self.command))
                    return ver
            return False
        except subproc.CalledProcessError:
            # This usually means the packet is not installed
            return False
        except Exception as ex:
            self.log.error("Parsing `{0} list installed` failed.".format(self.command))
            self.log.trace(str(ex))
        return False

    def install(self, pkgname):
        """
        zypper install pkgname
        """
        return self._run_cmd(pkgname, 'install')

    def update(self, pkgname):
        """
        zypper update pkgname
        """
        return self._run_cmd(pkgname, 'update')

    def _run_cmd(self, pkgname, cmd):
        """
        Call zypper with cmd.
        """
        try:
            subproc.monitor_process([self.command, cmd, "-y", pkgname], elevate=True)
            return True
        except Exception as ex:
            self.log.error("Running `{0} install' failed.".format(self.command))
            self.log.trace(str(ex))
            return False

class Zypper(ExternCmdPackagerBase):
    """
    zypper install xyz
    """
    name = 'zypper'
    pkgtype = 'rpm'

    def __init__(self):
        ExternCmdPackagerBase.__init__(self)
        self.packager = ExternalZypper(self.log)

    def supported(self):
        """
        Check if we can even run zypper.
        Return True if so.
        """
        return self.packager.command is not None

