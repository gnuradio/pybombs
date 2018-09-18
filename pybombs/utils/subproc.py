#
# Copyright 2015-2016 Free Software Foundation, Inc.
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

from __future__ import print_function
import os
import re
import signal
import subprocess
import threading
try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # Py3k
from pybombs.pb_logging import logger
from pybombs.pb_exception import PBException

READ_TIMEOUT = 0.1 # s

CalledProcessError = subprocess.CalledProcessError


def check_output(*args, **kwargs):
    """
    Identical to Python's subprocess.check_output(), with one difference:
    It will *always* return a string, never a byte string.
    This makes it work with string-based tools (e.g. regex stuff) across Python
    versions 2 and 3.
    """
    return subprocess.check_output(*args, **kwargs).decode('utf-8')


def get_child_pids(pid):
    """
    Returns a list of all child pids associated with this pid.
    """
    get_child_pids_cmd = ["ps", "-o", "pid", "--ppid", str(pid), "--no-headers"]
    try:
        children = check_output(get_child_pids_cmd).strip().split("\n")
    except (OSError, subprocess.CalledProcessError):
        return []
    return [int(child) for child in children]


def kill_process_tree(process, pid=None):
    """
    Kill the process and, if possible, all associated child processes.

    TODO make more portable.
    """
    if pid is None:
        pid = process.pid
    children = get_child_pids(pid)
    for child_pid in children:
        kill_process_tree(child_pid)
    if process is not None:
        try:
            process.terminate()
        except OSError:
            return
    else:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                return

def run_with_output_processing(p, o_proc, event, cleanup=None):
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
            line = q.get(timeout=READ_TIMEOUT).decode('utf-8')
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
            if cleanup is not None:
                cleanup()
            return 1
    o_proc.process_final()
    return p.returncode

def _process_thread(event, args, kwargs):
    """
    This actually runs the process.
    """
    def elevate_command(args, elevate_pre_args):
        " Modify the command to run with elevated privileges. "
        if isinstance(elevate_pre_args, str):
            elevate_pre_args = [elevate_pre_args,]
        if len(elevate_pre_args[0].strip()) == 0:
            elevate_pre_args = []
        if kwargs.get('shell', False) and isinstance(args, str):
            args = ' '.join(elevate_pre_args) + args
        else:
            args = elevate_pre_args + args
        return args
    def pretty_print_cmd(args):
        " Return pretty-printed version of the command. "
        if isinstance(args, list):
            return ' '.join(args)
        else:
            return "{sh}{cmd}".format(
                sh="$ " if kwargs.get('shell', False) else "",
                cmd=args.strip()
            )
    from pybombs.config_manager import config_manager
    from pybombs.utils import output_proc
    _process_thread.result = 0
    extra_popen_args = {}
    use_oproc = False
    o_proc = kwargs.get('o_proc')
    if isinstance(o_proc, output_proc.OutputProcessor):
        use_oproc = True
        extra_popen_args = o_proc.extra_popen_args
    if kwargs.get('shell', False) and isinstance(args, list):
        args = ' '.join(args)
    if kwargs.get('elevate'):
        args = elevate_command(args, config_manager.get('elevate_pre_args'))
    log = logger.getChild("_process_thread()")
    cmd_pp = pretty_print_cmd(args)
    if kwargs.get('elevate'):
        log.info("Executing command with elevated privileges: `{cmd}'"
                 .format(cmd=cmd_pp))
    else:
        log.debug("Executing command `{cmd}'".format(cmd=cmd_pp))
    try:
        proc = subprocess.Popen(
            args,
            shell=kwargs.get('shell', False),
            env=kwargs.get('env', config_manager.get_active_prefix().env),
            **extra_popen_args
        )
    except OSError:
        log.error("Failure executing command `{cmd}'!".format(cmd=cmd_pp))
        if kwargs.get('elevate'):
            log.debug("Make sure command can be elevated using `{epa}' " \
                           "on this platform!".format(
                               epa=config_manager.get('elevate_pre_args')))
        return -1
    if use_oproc:
        ret_code = run_with_output_processing(
            proc, o_proc,
            event, kwargs.get('cleanup')
        )
    else:
        # Wait until the process is done, or monitor_process() sends us the
        # quit event
        ret_code = None
        while ret_code is None and not event.is_set():
            ret_code = proc.poll()
            event.wait(1)
            if event.is_set():
                kill_process_tree(proc)
                if kwargs.get('cleanup') is not None:
                    kwargs.get('cleanup')()
                break
    _process_thread.result = ret_code
    event.set()
    return ret_code

# args is not *args!
def monitor_process(args, **kwargs):
    """
    Run a process and monitor it. If it is cancelled, perform cleanup.

    Params:
    - args: Must be a list (e.g. ['ls', '-l'])
    - shell: If True, run in shell environment
    - throw: Throw a PBException if the process returns a non-zero return value
    - throw_ex: If True, propagate subprocess exceptions. If False, return -1
                on exceptions.
    - env: A dictionary with environment variables.
           Note: If None is provided, it will actually load the environment
           from the config manager.
    - o_proc: An output processor
    - cleanup: A callback to clean up artifacts if the process is killed
    - elevate: Run with elevated privileges (e.g., 'sudo <command>')

    Returns the process's return value.
    """
    log = logger.getChild("monitor_process()")
    if kwargs.get('elevate'):
        log.debug("Running with elevated privileges.")
    try:
        quit_event = threading.Event()
        monitor_thread = threading.Thread(
            target=_process_thread,
            args=(quit_event, args, kwargs)
        )
        monitor_thread.start()
        while monitor_thread.isAlive:
            # Try if it's finished:
            monitor_thread.join(1)
            if quit_event.is_set() or not monitor_thread.is_alive():
                log.debug("Thread signaled termination or returned")
                break
        log.debug("Return value: {0}".format(_process_thread.result))
        if _process_thread.result != 0 and kwargs.get("throw", False):
            raise PBException("Process returned value: " + str(_process_thread.result))
        return _process_thread.result
    except KeyboardInterrupt:
        print("")
        log.info("Caught Ctrl+C. Killing all sub-processes.")
        quit_event.set()
        monitor_thread.join(15)
        raise KeyboardInterrupt
    except Exception as ex:
        if kwargs.get('throw_ex', False):
            raise ex
        else:
            return -1


def match_output(command, pattern, match_key=None, **kwargs):
    """
    Runs `command', and matches it against regex `pattern'.
    If there was a match, returns that, as a string.
    `match_key` is used to identify the match group key.

    **kwargs are passed straight to check_output().

    Note: This uses re.search(), not re.match()!
    """
    out = check_output(command, stderr=subprocess.STDOUT, **kwargs)
    try:
        return re.search(pattern, out, re.MULTILINE).group(match_key or 0)
    except AttributeError:
        return False

