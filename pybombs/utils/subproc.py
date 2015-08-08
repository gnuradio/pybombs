#!/usr/bin/env python2
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
Subprocess utils
"""

import subprocess
from pybombs.pb_logging import logger
from pybombs.config_manager import config_manager
from pybombs.utils import output_proc

def monitor_process(
            args,
            shell=False,
            throw_ex=False,
            env=None,
            o_proc=None,
    ):
    """
    Run a process and monitor it. If it is cancelled, perform
    cleanup. FIXME this feature doesn't actually exist yet.

    Params:
    - args: Must be a list (e.g. ['ls', '-l']
    - shell: If True, run in shell environment
    - throw_ex: If True, propagate subprocess exceptions FIXME currently doesn't do anything
    - env: A dictionary with environment variables. Note: If None is provided, it will
           actually load the environment from the config manager.
    - oproc: An output processor
    """
    log = logger.getChild("monitor_process()")
    log.debug("Executing command `{cmd}'".format(cmd=str(args).strip()))
    extra_popen_args = {}
    use_oproc = False
    if isinstance(o_proc, output_proc.OutputProcessor):
        use_oproc = True
        extra_popen_args = o_proc.extra_popen_args
    if env is None:
        env = config_manager.get_active_prefix().env
    p = subprocess.Popen(args, shell=shell, env=env, **extra_popen_args)
    if use_oproc:
        ret_code = output_proc.run_with_output_processing(p, o_proc)
    else:
        ret_code = p.wait()
    log.debug("monitor_process(): return value = {}".format(ret_code))
    return ret_code

