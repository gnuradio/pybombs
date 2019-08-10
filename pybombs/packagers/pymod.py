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
" Packager: python module "

import importlib
from pybombs.packagers.extern import ExternCmdPackagerBase, ExternReadOnlyPackager

class ExternalPythonModule(ExternReadOnlyPackager):
    " Wrapper around importlib "
    def __init__(self, logger):
        ExternReadOnlyPackager.__init__(self, logger)

    def get_installed_version(self, pkgname):
        """
        Use importlib to determine and return the currently installed version.
        If pkgname is not installed, return None.
        If we can import, but not determine a version, return True.
        """
        pkgname = pkgname.split('.', 1)
        if len(pkgname) == 2:
            pkgname, version_attr = pkgname
        else:
            pkgname, version_attr = pkgname[0], "__version__"
        try:
            module = importlib.import_module(pkgname)
            self.log.debug("Successfully imported Python module: {0}".format(pkgname))
        except ImportError:
            self.log.debug("Could not import Python module: {0}".format(pkgname))
            return False
        try:
            version = getattr(module, version_attr)
            self.log.debug("Module version: {0}.{1} == {2}".format(pkgname, version_attr, version))
        except AttributeError:
            return True
        return version

class PythonModule(ExternCmdPackagerBase):
    """
    Check to see if a Python module is installed.
    Can't install stuff, but is useful for finding out if
    something is already installed.
    """
    name = 'pymod'
    pkgtype = 'python'

    def __init__(self):
        ExternCmdPackagerBase.__init__(self)
        self.packager = ExternalPythonModule(self.log)

    def supported(self):
        " If we're running this, we can always check for Python modules. "
        return True

