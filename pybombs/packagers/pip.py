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
Packager: pip
"""

import re
from pybombs.packagers.extern import ExternCmdPackagerBase, ExternPackager
from pybombs.utils import sysutils
from pybombs.utils import subproc

PIP_INSTALLED_CACHE = None

class ExternalPip(ExternPackager):
    """
    Wrapper for pip
    """
    def __init__(self, logger):
        ExternPackager.__init__(self, logger)

    def get_available_version(self, pkgname):
        """
        See if 'pip search' finds our package.
        """
        try:
            output_match = subproc.match_output(
                ["pip", "search", pkgname],
                r'^\b{pkg}\b'.format(pkg=pkgname),
            )
            return bool(output_match)
        except subproc.CalledProcessError:
            return False
        except Exception as ex:
            self.log.error("Error running `pip search {0}`".format(pkgname))
            self.log.debug(ex)
        return False

    def get_installed_version(self, pkgname):
        """
        Return the currently installed version. If pkgname is not installed,
        return None.
        """
        global PIP_INSTALLED_CACHE
        if PIP_INSTALLED_CACHE is None:
            self.load_install_cache()
        return PIP_INSTALLED_CACHE.get(pkgname)

    def load_install_cache(self):
        """
        Populate the installed cache.
        """
        global PIP_INSTALLED_CACHE
        self.log.debug("Loading pip install cache.")
        PIP_INSTALLED_CACHE = {}
        try:
            installed_packages = str(subproc.check_output(["pip", "list"])).strip().split("\n")
            for pkg in installed_packages:
                mobj = re.match(r'(?P<pkg>\S+)\s+\((?P<ver>[^)]+)\)', str(pkg))
                if mobj is None:
                    continue
                PIP_INSTALLED_CACHE[mobj.group('pkg')] = mobj.group('ver')
            return
        except subproc.CalledProcessError as e:
            self.log.error("Could not run pip list. Hm.")
            self.log.error(str(e))
        except Exception as e:
            self.log.error("Some error while running pip list.")
            self.log.error(str(e))

    def install(self, pkgname):
        """
        yum/dnf install pkgname
        """
        return self._run_pip_install(pkgname)

    def update(self, pkgname):
        """
        yum/dnf update pkgname
        """
        return self._run_pip_install(pkgname, True)

    def _run_pip_install(self, pkgname, update=False):
        """
        Run pip install [--upgrade]
        """
        try:
            command = [sysutils.which('pip'), "install"]
            if update:
                command.append('--upgrade')
            command.append(pkgname)
            self.log.debug("Calling `{cmd}'".format(cmd=" ".join(command)))
            subproc.monitor_process(command, elevate=True)
            self.load_install_cache()
            return True
        except Exception as e:
            self.log.error("Running pip install failed.")
            self.log.debug(str(e))
        return None

class Pip(ExternCmdPackagerBase):
    """
    pip install xyz
    """
    name = 'pip'
    pkgtype = 'pip'

    def __init__(self):
        ExternCmdPackagerBase.__init__(self)
        self.packager = ExternalPip(self.log)

    def supported(self):
        """
        Check if we can even run 'pip'.
        Return True if so.
        """
        return sysutils.which('pip') is not None

