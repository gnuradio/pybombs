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
Packager: port
"""

import re
import subprocess
from pybombs.packagers.extern import ExternCmdPackagerBase, ExternPackager
from pybombs.utils import subproc
from pybombs.utils import sysutils

class ExternalPort(ExternPackager):
    """
    Wrapper around port
    """
    def __init__(self, logger):
        ExternPackager.__init__(self, logger)

    def get_available_version(self, pkgname):
        """
        Search for package with 'port search'
        """
        try:
            out = subproc.check_output(["port", "search", "--name", "--glob", pkgname]).strip()
            if "No match" in out:
                return False
            ver = re.search(r'@(?P<ver>[0-9,.]*)', str(out)).group('ver')
            return ver
        except subprocess.CalledProcessError:
            return False
        except Exception as e:
            self.log.error("Error running port search")
        return False

    def get_installed_version(self, pkgname):
        """
        Retrun installed version. Return False if package is not installed
        """
        try:
            out = subproc.check_output(["port", "installed", pkgname]).strip()
            if "None of the specified ports" in out:
                return False
            ver = re.search(r'@(?P<ver>[0-9,.]*)', str(out)).group('ver')
            return ver
        except subprocess.CalledProcessError:
            # This usually means the packet is not installed -- not a problem.
            return False
        except Exception as e:
            self.log.error("Running port installed failed.")
            self.log.obnoxious(str(e))

    def install(self, pkgname):
        """
        Install package with 'port install'
        """
        try:
            subproc.monitor_process(["port", "install", pkgname], elevate=True, throw=True)
            return True
        except Exception as ex:
            self.log.error("Running port install failed.")
            self.log.obnoxious(str(ex))
            return False

    def update(self, pkgname):
        """
        update package with 'port upgrade'
        """
        try:
            subproc.monitor_process(["port", "upgrade", pkgname], elevate=True, throw=True)
            return True
        except Exception as ex:
            self.log.error("Running port upgrade failed.")
            self.log.obnoxious(str(ex))

class Port(ExternCmdPackagerBase):
    """
    port install package
    """
    name = 'port'
    pkgtype = 'port'

    def __init__(self):
        ExternCmdPackagerBase.__init__(self)
        self.packager = ExternalPort(self.log)

    def supported(self):
        """
        Check if macports is installed
        """
        return sysutils.which('port') is not None
