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
OS Module: Ubuntu
"""

import re
import subprocess
from pybombs.packagers.base import PackagerBase

class Ubuntu(PackagerBase):
    name = 'apt-get'
    def __init__(self):
        PackagerBase.__init__(self)

    def satisfy(self, pkgname, version):
        pass

    def supported():
        """ Return true if this platform is detected """
        # Check to make sure that dpkg, apt-cache and apt-get are installed
        '''
        def have_debs(pkg_expr_tree):
            if(which("dpkg") == None):
                return False;
            if(pkg_expr_tree):
                return pkg_expr_tree.ev(have_deb);
            return False;

        def debs_exist(pkg_expr_tree):
            if(which("apt-cache") == None):
                return False
            if(pkg_expr_tree):
                return pkg_expr_tree.ev(deb_exists);
            return False
        '''

    def exists(self, name, throw_ex=True):
        """
        Checks to see if a package is avaliable in apt-get and returns the verion.
        If package does not exist, throw an exception.
        """

        try:
            out = subprocess.check_output(["apt-cache", "showpkg", name])
            # apt-cache returns nothing on stdout if a package is not found
            if len(out) >= 0:
                # Get the versions
                ver = re.search(r'Versions: \n(\d+:)?([0-9]+\.[0-9]+\.[0-9]+|[0-9]+\.[0-9]+|[0-9]+[a-z]+|[0-9]+).*\n', out)
                return ver.group(2)
            else:
                msg = "Unknown package"
        except subprocess.CalledProcessError, e:
            # Non-zero return.
            msg = "Call to showpkg failed"
        except:
            # The subprocess call failed
            msg = "Subprocess call failed"

        # Determine the correct output method
        if throw_ex:
            raise Exception(msg)
        return False

    def install(self, name, throw_ex=True):
        try:
            out = subprocess.check_output(["sudo", "apt-get", "-y", "install", name])
            return True
        except subprocess.CalledProcessError, e:
            # Non-zero return.
            msg = "Call to showpkg failed"
        except:
            # The subprocess call failed
            msg = "Subprocess call failed"

        # Determine the correct output method
        if throw_ex:
            raise Exception(msg)
        return False

    def installed(self, name, throw_ex=True):
        try:
            out = subprocess.check_output(["dpkg", "-s", name])

            # Get the versions
            ver = re.search(r'Version: (\d+:)?([0-9]+\.[0-9]+\.[0-9]+|[0-9]+\.[0-9]+|[0-9]+[a-z]+|[0-9]+).*\n', out)
            return ver.group(2)
        except subprocess.CalledProcessError, e:
            # Non-zero return.
            msg = "Call to showpkg failed"
        except:
            # The subprocess call failed
            msg = "Subprocess call failed"

        # Determine the correct output method
        if throw_ex:
            raise Exception(msg)
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

ubuntu = Ubuntu()

# Some test code:
if __name__ == "__main__":
    print ubuntu.exists("gcc")
    print ubuntu.installed("gcc")
    print ubuntu.install("gcc")
    print ubuntu.exists("test", throw_ex=False)
    print ubuntu.installed("test", throw_ex=False)
    print ubuntu.install("test", throw_ex=False)
    print ubuntu.exists("test")
