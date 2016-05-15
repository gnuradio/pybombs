#
# Copyright 2016 Free Software Foundation, Inc.
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
Packager: pacman
"""

import subprocess
from pybombs.packagers.extern import ExternCmdPackagerBase, ExternPackager
from pybombs.utils import subproc
from pybombs.utils import sysutils

class ExternalPacman(ExternPackager):
    """
    Wrapper for pacman
    """
    def __init__(self, logger):
        ExternPackager.__init__(self, logger)
        self.command = None
        if sysutils.which('pacman') is not None:
            self.command = 'pacman'

    def get_available_version(self, pkgname):
        """
        Return a version that we can install through this package manager.
        """
        try:
            ver = subproc.match_output(
                [self.command, "-Si", pkgname],
                r'Version[ ]*: (?P<ver>[0-9,.]*)',
                'ver'
            ) or False
            if ver:
                self.log.debug("Package {} has version {} in {}".format(pkgname, ver, self.command))
            return ver
        except subprocess.CalledProcessError as ex:
            # This usually means the package was not found, so don't worry
            self.log.obnoxious("`{0} -Si' returned non-zero exit status.".format(self.command))
            self.log.obnoxious(str(ex))
            return False
        except Exception as ex:
            self.log.error("Error parsing {0} -Si".format(self.command))
            self.log.error(str(ex))
        return False

    def get_installed_version(self, pkgname):
        """
        Return the currently installed version. If pkgname is not installed,
        return None.
        """
        try:
            # '-Qi' will return non-zero if package does not exist, thus will throw
            # Output is sth like local/<pkgname> x.x.x.x-x
            ver = subproc.match_output(
                [self.command, "-Si", pkgname],
                r'Version[ ]*: (?P<ver>[0-9,.]*)',
                'ver'
            )
            if ver is None:
                self.log.debug("Looks like pacman -Qi can't find package {pkg}".format(pkg=pkgname))
                return False
            self.log.debug("Package {} has version {}".format(pkgname, ver))
            return ver
        except subprocess.CalledProcessError:
            # This usually means the packet is not installed
            return False
        except Exception as ex:
            self.log.error("Parsing `{0} -Qi` failed.".format(self.command))
            self.log.obnoxious(str(ex))
        return False

    def install(self, pkgname):
        """
        pacman install pkgname
        """
        return self._run_cmd(pkgname, '-S')

    def update(self, pkgname):
        """
        pacman update pkgname
        """
        return self._run_cmd(pkgname, '-S')

    def _run_cmd(self, pkgname, cmd):
        """
        Call pacman with cmd.
        """
        try:
            subproc.monitor_process([self.command, "--noconfirm", cmd, pkgname], elevate=True)
            return True
        except Exception as ex:
            self.log.error("Running `{} {}' failed.".format(self.command, cmd))
            self.log.obnoxious(str(ex))
            return False

class Pacman(ExternCmdPackagerBase):
    """
    pacman install xyz
    """
    name = 'pacman'
    pkgtype = 'pacman'

    def __init__(self):
        ExternCmdPackagerBase.__init__(self)
        self.packager = ExternalPacman(self.log)

    def supported(self):
        """
        Check if we can even run pacman.
        Return True if so.
        """
        return self.packager.command is not None

