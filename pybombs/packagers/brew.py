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
Packager: homebrew
"""

import json
import subprocess
from pybombs.packagers.extern import ExternCmdPackagerBase, ExternPackager
from pybombs.utils import subproc
from pybombs.utils import sysutils
from pybombs.utils.vcompare import vcompare


class ExternalHomebrew(ExternPackager):
    def __init__(self, logger):
        ExternPackager.__init__(self, logger)

    def get_available_version(self, pkgname):
        """
        Check which version is currently installed.
        """
        try:
            self.log.obnoxious("Checking homebrew for `{0}'".format(pkgname))
            out = subprocess.check_output(["brew", "info", "--json=v1", pkgname])
            # Returns non-zero exit status if package does not exist in brew taps
            if len(out) >= 0:
                # Get the version.
                pkgdata = json.loads(out)[0]  # Wrapped in a list. get the first element.
                version = pkgdata["versions"]["stable"]
                return version
            else:
                return False
        except subprocess.CalledProcessError:
            # This usually means the packet is not installed
            return False
        except Exception as e:
            self.log.error("Running brew info failed.")
            self.log.obnoxious(str(e))
        return False

    def get_installed_version(self, pkgname):
        """
        Check which version has been installed by brew.
        Note: By default, homebrew does not uninstall old versions of packages.
        Figure out which version is the newest.
        If older versions of the package exist, tell the user they may want to run "brew cleanup".?
        """
        try:
            self.log.obnoxious("Checking homebrew for `{0}'".format(pkgname))
            out = subprocess.check_output(["brew", "info", "--json=v1", pkgname])
            # Returns non-zero exit status if package does not exist in brew taps
            if len(out) >= 0:
                # Get the version.
                pkgdata = json.loads(out)[0]  # Wrapped in a list. get the first element.
                installed = pkgdata["installed"]
                if len(installed) > 0:
                    version = installed[0]["version"]
                else:
                    return False
                self.log.obnoxious("{0} version {1} installed through homebrew".format(pkgname, version))
                return version
            else:
                return False
        except subprocess.CalledProcessError as e:
            self.log.error("Unable to find package")
        except KeyError as e:
            self.log.error("Package is not installed")
        except Exception as e:
            # Non-zero return.
            self.log.error("Error running brew info")
            self.log.error(repr(e))
        return False

    def install(self, pkgname):
        """
        Call 'brew install pkgname' if we can satisfy the version requirements.
        """
        try:
            # Need to do some better checking here. Brew does not necessarily need sudo
            #sysutils.monitor_process(["sudo", "brew", "", "install", pkg_name])
            subproc.monitor_process(["brew", "install", pkgname])
            return True
        except Exception as e:
            #self.log.obnoxious(e)
            self.log.error("Running brew install failed.")
        return False


class Homebrew(ExternCmdPackagerBase):
    """
    brew install xyz
    """
    name = 'brew'
    pkgtype = 'brew'

    def __init__(self):
        ExternCmdPackagerBase.__init__(self)
        self.packager = ExternalHomebrew(self.log)

    def supported(self):
        """
        Check if homebrew exists
        Return True if so.
        """
        return sysutils.which('brew') is not None
