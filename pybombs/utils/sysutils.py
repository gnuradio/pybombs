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
import subprocess
from threading import Thread,Event
from pybombs.pb_logging import logger

log = logger.getChild("SysUtils")

def which(program):
    """
    Equivalent to Unix' `which` command.
    Returns None if the executable `program` can't be found.
    """
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None


#def monitor_process_timeout(proc, timeout, shell=False, throw_ex=False):

def monitor_process(
            args,
            shell=False,
            throw_ex=False,
            env=None,
            oproc=None,
    ):
    """
    Run a process and monitor it.

    Params:
    - args: Must be a list (e.g. ['ls', '-l']
    - shell: If True, run in shell environment
    - throw_ex: If True, propagate subprocess exceptions
    - env: A dictionary with environment variables
    - oproc: An output processor
    """
    # FIXME write this
    log.debug("monitor_process(): Executing command {}".format(" ".join(args)))
    try:
        subprocess.check_call(args, shell=shell, env=env)
    except subprocess.CalledProcessError as e:
        if throw_ex:
            raise e
        return -1

if __name__ == "__main__":
    monitor_process(["ls", "-l", "-h"])
    monitor_process(["ls", "-l", "-h"], shell=True)
    env = {'FOO': 'BAR'}
    monitor_process(["env",], env=env)

