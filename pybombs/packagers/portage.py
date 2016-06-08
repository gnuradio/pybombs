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
Packager: portage
"""

import subprocess
from pybombs.packagers.extern import ExternCmdPackagerBase, ExternPackager
from pybombs.utils import subproc
from pybombs.utils import sysutils

class ExternalPortage(ExternPackager):
    """
    Wrapper for portage
    """
    def __init__(self, logger):
        ExternPackager.__init__(self, logger)
        self.available = False
        try:
            from _emerge import search
            from _emerge import actions
            from _emerge.actions import load_emerge_config
            self.portage = __import__('portage')
            emerge_config = load_emerge_config()
            self.root_config = emerge_config.running_config
            # search init args:
            # (self,root_config,spinner,searchdesc,verbose,usepkg,usepkgconly,search_index=True)
            self.search = search.search(self.root_config,False,False,False,True,False)
            self.search._vardb.cp_all()
            self.available = True
        except ImportError as e:
            self.available = False

    def get_available_version(self, pkgname):
        """
        Return a version that we can install through this package manager.
        """
        try:
            ver = None
            pkg = self.search._xmatch('bestmatch-visible',pkgname)
            ver = self.portage.catpkgsplit(pkg, True)[2]
            if ver:
                self.log.debug("Package {} has version {} in portage".format(pkgname, ver))
            return ver
        except Exception as ex:
            self.log.error("Error: {}".format(ex))
        return False

    def get_installed_version(self, pkgname):
        """
        Return the currently installed version. If pkgname is not installed,
        return None.
        """
        try:
            installed_package = self.search._vardb.match(pkgname)
            if installed_package:
                try:
                    self._vardb.match_unordered
                except AttributeError:
                    installed_package = installed_package[-1]
                else:
                    installed_package = self.portage.best(installed_package)
            else:
                installed_package = ""
            if installed_package:
                ver = self.portage.catpkgsplit(installed_package,True)[2]
                self.log.debug("Package {} has version {}".format(pkgname, ver))
            else:
                ver = None
            #print('Portage ver: {}'.format(ver))
            return ver
        except Exception as ex:
            self.log.error("Error: `{} ".format(ex))
            self.log.obnoxious(str(ex))
            return False

    def install(self, pkgname):
        """
        pacman install pkgname
        """
        return NotImplementedError

    def update(self, pkgname):
        """
        pacman update pkgname
        """
        return NotImplementedError

class Portage(ExternCmdPackagerBase):
    """
     portage install xyz
    """
    name = 'portage'
    pkgtype = 'portage'

    def __init__(self):
        ExternCmdPackagerBase.__init__(self)
        self.packager = ExternalPortage(self.log)

    def supported(self):
        """
        Check if we have portage python bindings.
        Return True if so.
        """
        return self.packager.available
