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
Packager Module: Dummy Packager
"""

from pybombs import pb_logging

class Dummy(object):
    """
    This isn't really a packager, this is just a dummy load
    for testing functions that require packagers.
    """
    def __init__(self):
        self.log = pb_logging.logger.getChild('dummy')

    def satisfy(self, pkgname, version):
        pass

    def supported():
        """ Return true if this platform is detected """
        return True

    def exists(self, name, throw_ex=True):
        """
        We'll always return version 0.0 here.
        """
        self.log.info("Pretending that package {} exists.".format(name))
        return "0.0"

    def install(self, name, throw_ex=True):
        """
        Pseudo-install package
        """
        self.log.info("Pretending to install package {}.".format(name))
        return True

    def installed(self, name, throw_ex=True):
        """
        We always pretend the package is not yet installed
        """
        return False

    def execute(self, name):
        """
        Checks to see if a package is avaliable in apt-get and returns the verion.
        If package does not exist, throw an exception.
        """

        try:
            if not isinstance(cmd, list):
                cmd = [cmd]
            out = subprocess.check_output(cmd)
            return out
        except subprocess.CalledProcessError, e:
            return False
        except:
            return False

    # stdout -> return
    def execute_err(cmd, throw=True):
        try:
            if not isinstance(cmd, list):
                cmd = [cmd]
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=pb_globals.env);
            (out,err) = p.communicate();
            return out;
        except Exception, e:
            if(throw_ex):
                raise e;
            else:
                return -1;

# Some test code:
if __name__ == "__main__":
    print ubuntu.exists("gcc")
    print ubuntu.installed("gcc")
    print ubuntu.install("gcc")
    print ubuntu.exists("test", throw_ex=False)
    print ubuntu.installed("test", throw_ex=False)
    print ubuntu.install("test", throw_ex=False)
    print ubuntu.exists("test")

