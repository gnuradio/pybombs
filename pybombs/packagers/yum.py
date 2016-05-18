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
Packager: yum or dnf
"""

import re
import subprocess
from pybombs.packagers.extern import ExternCmdPackagerBase, ExternPackager
from pybombs.utils import subproc
from pybombs.utils import sysutils

class ExternalYumDnf(ExternPackager):
    """
    Wrapper for yum or dnf
    """
    def __init__(self, logger):
        ExternPackager.__init__(self, logger)
        self.command = None
        if sysutils.which('dnf') is not None:
            self.command = 'dnf'
        elif sysutils.which('yum') is not None:
            self.command = 'yum'

    def get_available_version(self, pkgname):
        """
        Return a version that we can install through this package manager.
        """
        try:
            ver = subproc.match_output(
                [self.command, "info", pkgname],
                r'^Version\s+:\s+(?P<ver>.*$)',
                'ver'
            )
            if ver is None:
                return False
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
        Return the currently installed version. If pkgname is not installed,
        return False.
        """
        pkgarch = None
        if pkgname.find('.') != -1:
            pkgname, pkgarch = pkgname.split('.', 1)
        try:
            # 'list installed' will return non-zero if package does not exist, thus will throw
            out = subproc.check_output(
                    [self.command, "list", "installed", pkgname],
                    stderr=subprocess.STDOUT
            ).strip().split("\n")
            # Output looks like this:
            # <pkgname>.<arch>   <version>   <more info>
            # So, two steps:
            # 1) Check that pkgname is correct (and, if necessary, the package arch)
            # 2) return version
            for line in out:
                mobj = re.match(r"^(?P<pkg>[^\.]+)\.(?P<arch>\S+)\s+(\d+:)?(?P<ver>[0-9]+(\.[0-9]+){0,2})", line)
                if mobj and mobj.group('pkg') == pkgname:
                    if pkgarch is not None and mobj.group('arch') != pkgarch:
                        continue
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

    def install(self, pkgname):
        """
        yum/dnf install pkgname
        """
        return self._run_cmd(pkgname, 'install')

    def update(self, pkgname):
        """
        yum/dnf update pkgname
        """
        return self._run_cmd(pkgname, 'update')

    def _run_cmd(self, pkgname, cmd):
        """
        Call yum or dnf with cmd.
        """
        try:
            subproc.monitor_process([self.command, "-y", cmd, pkgname], elevate=True)
            return True
        except Exception as ex:
            self.log.error("Running `{0} install' failed.".format(self.command))
            self.log.obnoxious(str(ex))
            return False

class YumDnf(ExternCmdPackagerBase):
    """
    yum/dnf install xyz
    """
    name = 'yumdnf'
    pkgtype = 'rpm'

    def __init__(self):
        ExternCmdPackagerBase.__init__(self)
        self.packager = ExternalYumDnf(self.log)

    def supported(self):
        """
        Check if we can even run yum or dnf.
        Return True if so.
        """
        return self.packager.command is not None

