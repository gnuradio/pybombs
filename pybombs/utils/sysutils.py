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

from __future__ import print_function
import os
import os.path as op
from pybombs.pb_exception import PBException

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

def dir_is_writable(dir_path):
    " Returns True if dir_path is a writable directory "
    return op.isdir(dir_path) and os.access(dir_path, os.W_OK|os.X_OK)

def mkdir_writable(dir_path, log=None):
    """
    Create a directory if it doesn't yet exist.
    Returns True if that worked and the dir is writable.
    """
    if not op.isdir(dir_path):
        if log is not None:
            log.info("Creating directory `{0}'".format(dir_path))
        os.mkdir(dir_path)
    return dir_is_writable(dir_path)

def mkdirp_writable(dir_path, log=None):
    """
    Like mkdir_writable(), but creates all parents if necessary (like mkdir -p)
    """
    if dir_is_writable(dir_path):
        return True
    parent = os.path.split(dir_path)[0]
    if len(parent) != 0:
        if not mkdirp_writable(parent, log):
            return False
    return mkdir_writable(dir_path, log)

def require_subdirs(base_path, subdirs, log=None):
    """
    subdirs is a list of subdirectories that need to exist inside path.

    If this is satisfied, returns True.
    """
    if not dir_is_writable(base_path):
        if log:
            log.error("Base path {0} does not exist".format(base_path))
        return False
    common_prefix = os.path.commonprefix(
        [os.path.normpath(os.path.join(base_path, x)) for x in subdirs]
    )
    if not op.normpath(common_prefix) in op.normpath(base_path):
        raise PBException("Invalid subdir list (going outside base path)")
    return all([mkdirp_writable(os.path.join(base_path, subdir), log) for subdir in subdirs])

def write_file_in_subdir(base_path, file_path, content):
    """
    Write 'content' to a file. The absolute path to the file comes from
    joining base_path and file_path. However, if file_path tries to go
    outside base_path, an exception is raised.
    """
    abs_file_path = os.path.join(base_path, file_path)
    if not op.normpath(base_path) in op.normpath(abs_file_path):
        raise PBException("Attempting write to file outside base_path")
    open(abs_file_path, 'w').write(content)


if __name__ == "__main__":
    print(which("vim"))

