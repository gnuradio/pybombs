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
System Utils
"""

import os

def which(program, env=None):
    """
    Equivalent to Unix' `which` command.
    Returns None if the executable `program` can't be found.

    If a full path is given (e.g. /usr/bin/foo), it will return
    the path if the executable can be found, or None otherwise.

    If no path is given, it will search PATH.
    """
    def is_exe(fpath):
        " Check fpath is an executable "
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
    if env is None:
        env = os.environ
    if os.path.split(program)[0] and is_exe(program):
        return program
    else:
        for path in os.environ.get("PATH", "").split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None

if __name__ == "__main__":
    print(which("vim"))

