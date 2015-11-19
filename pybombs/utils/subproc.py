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

import os
import time
import signal
import subprocess
import threading
try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # Py3k
from pybombs.pb_logging import logger
from pybombs.config_manager import config_manager
from pybombs.utils import output_proc

READ_TIMEOUT = 0.1 # s

def kill_process_tree(process, pid=None):
    """
    Kill the process and, if possible, all associated child processes.

    TODO make more portable.
    """
    if pid is None:
        pid = process.pid
    try:
        children = subprocess.check_output(
            "ps -o pid --ppid {pid} --noheaders".format(pid=pid),
            shell=True,
        )
    except (OSError, subprocess.CalledProcessError):
        children = ""
    if len(children) > 0:
        children = children.strip().split("\n")
        for child in children:
            kill_process_tree(None, int(child))
    if process is not None:
        process.terminate()
    else:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass

def run_with_output_processing(p, o_proc, event):
    """
    Run a previously created process p through
    an output processor o_proc.
    """
    def enqueue_output(stdout_data, stdout_queue, stderr_data, stderr_queue):
        " Puts the output from the process into the queue "
        for line in iter(stdout_data.readline, b''):
            stdout_queue.put(line)
        stdout_data.close()
        if stderr_data is not None:
            for line in iter(stderr_data.readline, b''):
                stderr_queue.put(line)
            stderr_data.close()
    def poll_queue(q):
        " Safe polling from queue "
        line = ""
        try:
            line = q.get(timeout=READ_TIMEOUT)
        except Empty:
            return ""
        # Got line:
        return line
    # Init thread and queue
    q_stdout = Queue()
    q_stderr = Queue()
    t = threading.Thread(target=enqueue_output, args=(p.stdout, q_stdout, p.stderr, q_stderr))
    # End the thread when the program terminates
    t.daemon = True
    t.start()
    # Run loop
    while p.poll() is None: # Run while process is alive
        line_stdout = poll_queue(q_stdout)
        line_stderr = poll_queue(q_stderr)
        o_proc.process_output(line_stdout, line_stderr)
        event.wait(0.05)
        if event.is_set():
            kill_process_tree(p)
            return 1
    o_proc.process_final()
    return p.returncode

def _process_thread(event, args, kwargs):
    """
    This actually runs the process.
    """
    _process_thread.result = 0
    log = logger.getChild("monitor_process()")
    extra_popen_args = {}
    use_oproc = False
    o_proc = kwargs.get('o_proc')
    if isinstance(o_proc, output_proc.OutputProcessor):
        use_oproc = True
        extra_popen_args = o_proc.extra_popen_args
    proc = subprocess.Popen(
        args,
        shell=kwargs.get('shell', False),
        env=kwargs.get('env', config_manager.get_active_prefix().env),
        **extra_popen_args
    )
    if use_oproc:
        ret_code = run_with_output_processing(proc, o_proc, event)
    else:
        # Wait until the process is done, or monitor_process() sends us the quit event
        ret_code = None
        while ret_code is None and not event.is_set():
            ret_code = proc.poll()
            event.wait(1)
            if event.is_set():
                kill_process_tree(proc)
                break
    _process_thread.result = ret_code
    log = logger.getChild("monitor_process()")
    log.debug("monitor_process(): return value = {}".format(ret_code))
    event.set()
    return ret_code

def monitor_process(
        args,
        **kwargs
    ):
    """
    Run a process and monitor it. If it is cancelled, perform
    cleanup. FIXME this feature doesn't actually exist yet.

    Params:
    - args: Must be a list (e.g. ['ls', '-l'])
    - shell: If True, run in shell environment
    - throw_ex: If True, propagate subprocess exceptions
                FIXME currently doesn't do anything
    - env: A dictionary with environment variables.
           Note: If None is provided, it will actually load the environment
           from the config manager.
    - oproc: An output processor
    - cleanup: A callback to clean up artifacts
    """
    log = logger.getChild("monitor_process()")
    log.debug("Executing command `{cmd}'".format(cmd=str(args).strip()))
    try:
        quitEvent = threading.Event()
        monitorThread = threading.Thread(
            target=_process_thread,
            args=(quitEvent, args, kwargs)
        )
        monitorThread.start()
        while monitorThread.isAlive:
            # Try if it's finished:
            monitorThread.join(1)
            if quitEvent.isSet():
                # TODO clean up this line
                log.debug("monitor_process(): Caught the quit Event")
                break
        return _process_thread.result
    except KeyboardInterrupt:
        print("")
        log.info("Caught Ctrl+C. Killing all sub-processes.")
        quitEvent.set()
        monitorThread.join()
        print('sleep')
        time.sleep(2)
        exit(0)
    except Exception as ex:
        if kwargs.get('throw_ex'):
            raise ex
        else:
            return -1

