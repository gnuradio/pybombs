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
Packager: pkg-config
"""

import subprocess
from pybombs.packagers.extern import ExternCmdPackagerBase, ExternReadOnlyPackager
from pybombs.utils import sysutils
from pybombs.utils import subproc

class ExternalPkgConfig(ExternReadOnlyPackager):
    """
    Wrapper around pkg-config
    """
    def __init__(self, logger):
        ExternReadOnlyPackager.__init__(self, logger)

    def get_installed_version(self, pkgname):
        """
        Use pkg-config to determine and return the currently installed version.
        If pkgname is not installed, return None.
        """
        try:
            # pkg-config will return non-zero if package does not exist, thus will throw
            ver = subproc.check_output(["pkg-config", "--modversion", pkgname], stderr=subprocess.STDOUT).strip()
            self.log.debug("Package {0} has version {1} in pkg-config".format(pkgname, ver))
            return ver
        except subprocess.CalledProcessError:
            # This usually means the packet is not installed
            return False
        except Exception as e:
            self.log.error("Running `pkg-config --modversion` failed.")
            self.log.obnoxious(str(e))
        return False


class PkgConfig(ExternCmdPackagerBase):
    """
    Uses pkg-config. Can't really install stuff, but is useful for
    finding out if something is already installed.
    """
    name = 'pkgconfig'
    pkgtype = 'pkgconfig'

    def __init__(self):
        ExternCmdPackagerBase.__init__(self)
        self.packager = ExternalPkgConfig(self.log)

    def supported(self):
        """
        Check if we can even run 'pkg-config'. Return True if yes.
        """
        return sysutils.which('pkg-config') is not None

