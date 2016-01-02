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
import subprocess
from pybombs.packagers.base import PackagerBase
from pybombs.utils import sysutils
from pybombs.utils import subproc
from pybombs.utils.vcompare import vcompare

PIP_INSTALLED_CACHE = None

class Pip(PackagerBase):
    """
    pip install xyz
    """
    name = 'pip'
    pkgtype = 'pip'

    def __init__(self):
        PackagerBase.__init__(self)

    def supported(self):
        """
        Check if we can even run 'pip'.
        Return True if so.
        """
        return sysutils.which('pip') is not None

    def _package_exists(self, pkgname, comparator=">=", required_version=None):
        """
        See if an installable version of pkgname matches the version requirements.
        """
        if self._package_installed(pkgname, comparator, required_version):
            self.log.debug("Package {pkg} available through pip.".format(pkg=pkgname))
            return True
        # We'll assume if it's in pip we have the latest version, so no more checks.
        return self.check_package_in_pip(pkgname)

    def _package_installed(self, pkgname, comparator=">=", required_version=None):
        """
        See if the installed version of pkgname matches the version requirements.
        """
        global PIP_INSTALLED_CACHE
        if PIP_INSTALLED_CACHE is None:
            self.load_install_cache()
        installed_version = PIP_INSTALLED_CACHE.get(pkgname)
        if not installed_version:
            return False
        if required_version is None or vcompare(comparator, installed_version, required_version):
            self.log.debug("Package {pkg} already installed by pip.".format(pkg=pkgname))
            return True
        return False

    def _package_install(self, pkgname, comparator=">=", required_version=None, update=False):
        """
        Call 'pip install pkgname' if we can satisfy the version requirements.
        """
        try:
            self.log.debug("Calling `pip install {pkg}'".format(pkg=pkgname))
            command = [sysutils.which('pip'), "install"]
            if update:
                command.append('--upgrade')
            command.append(pkgname)
            subproc.monitor_process(command, elevate=True)
            self.load_install_cache()
            installed_version = PIP_INSTALLED_CACHE.get(pkgname)
            self.log.debug("Installed version for {pkg} is: {ver}.".format(pkg=pkgname, ver=installed_version))
            if installed_version is None:
                return False
            if required_version is None:
                return True
            print required_version, comparator, installed_version
            return vcompare(comparator, installed_version, required_version)
        except Exception as e:
            self.log.error("Running pip install failed.")
            self.log.error(str(e))
        return False

    def _package_update(self, pkgname, comparator=">=", required_version=None):
        """
        Call 'pip install --upgrade pkgname' if we can satisfy the version requirements.
        """
        return self._package_install(pkgname, comparator, required_version, update=True)

    ### pip specific functions:
    def check_package_in_pip(self, pkgname):
        """
        See if 'pip search' finds our package.
        """
        try:
            out = subprocess.check_output(["pip", "search", pkgname]).strip()
            if len(out) == 0:
                return True
            out = out.split("\n")
            for line in out:
                if re.match(pkgname, line):
                    return True
        except subprocess.CalledProcessError:
            return False
        except Exception as e:
            self.log.error("Error running pip search")
        return False

    def get_installed_version(self, pkgname):
        """
        Check which version is currently installed.
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
            installed_packages = subprocess.check_output(["pip", "list"]).strip().split("\n")
            for pkg in installed_packages:
                mobj = re.match(r'(?P<pkg>\S+)\s+\((?P<ver>[^)]+)\)', pkg)
                if mobj is None:
                    continue
                PIP_INSTALLED_CACHE[mobj.group('pkg')] = mobj.group('ver')
            return
        except subprocess.CalledProcessError as e:
            self.log.error("Could not run pip list. Hm.")
            self.log.error(str(e))
        except Exception as e:
            self.log.error("Some error while running pip list.")
            self.log.error(str(e))
        exit(1)

