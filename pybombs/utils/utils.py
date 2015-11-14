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
utils
"""

from threading import Thread, Event
from copy import deepcopy
import os
import re
import shutil
import time
import glob
import copy
import signal
import operator
import sys
import subprocess
from pybombs import pb_logging

log = pb_logging.logger.getChild("utils")


#############################################################################
# Execute other scripts
#############################################################################


def get_child_pids(pid):
    """
    Returns a list of all child pids associated with this pid.
    """
    get_child_pids_cmd = ["ps", "-o", "pid", "--ppid", str(pid), "--no-headers"]
    try:
        children = subprocess.check_output(get_child_pids_cmd).strip().split("\n")
    except subprocess.CalledProcessError as e:
        return []
    return [int(child) for child in children]

def kill_process_tree(pid, process=None):
    """
    Recursively kills process and all associated child processes.
    """
    log.debug("kill_process_tree(): Killing pid {}".format(pid))
    children = get_child_pids(pid)
    log.debug("kill_process_tree(): Found children: {}".format(children))
    for child_pid in children:
        kill_process_tree(child_pid)
    # Kill:
    if process:
        process.terminate()
    else:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass

def monitor(cmd, event):
    """
    Execute cmd and monitor it.
    """
    # get the artifact to look for
    artifact = None
    if cmd[0:4] == "wget":
        r = re.search(r'.+/(.+)',cmd)
        artifact = r.group(1)
    elif cmd[0:9] == "git clone" or cmd[0:6] == "svn co":
        r = re.search(r'.+ (.+)',cmd)
        artifact = r.group(1)

    for tries in range(10):
        log.info("monitor(): Tried command %d time(s)" % (tries))
        if tries > 0:
            if cmd[0:4] == "wget":
                # clean up any truncated files
                [try_unlink(f) for f in glob.glob("%s.*" % (cmd.split('/')[-1:][0])) + [cmd.split('/')[-1:][0]]]
            elif cmd[0:9] == "git clone":
                rmrf(cmd.split(' ')[-1])
            elif cmd[0:6] == "svn co":
                svnclean(cmd.split(' ')[-1])
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, env=config_manager.env)
        pid = p.pid
        parentPid = pid
        while p.poll() == None:
            event.wait(1)
        if event.isSet():
            log.info("monitor: Caught the quit Event. Killing Subprocess...")
            kill_process_tree(p, pid)
            return
        if cmd[0:9] == "git clone":
            # check for subprocess started by the git subprocess
            try:
                child_pids = get_child_pids(pid)
                if len(child_pids) > 0:
                    pid = child_pids[0]
                    grandchild_pids = get_child_pids(pid)
                    if len(grandchild_pids) > 0:
                        pid = grandchild_pids[0]
            except subprocess.CalledProcessError:
                pass
        monitorCmd = "ps --noheaders -p %d -o time" % (pid)
        cpuUsageCmd = "ps --noheaders -p %d -o pcpu" % (pid)
        wgetCheckCmd = "ls -s %s" % (artifact)
        gitCheckCmd = "du -s %s" % (artifact)
        oldCpuTime = oldWgetSize = oldGitSize = "0"
        while True:
            retcode = p.poll()
            if retcode is not None:
                if retcode != 0 and tries < 10:
                    break
                else:
                    monitor.result = retcode
                    event.set()
                    return
            try:
                newCpuTime = subprocess.Popen(monitorCmd, shell=True, stdout=subprocess.PIPE).communicate()[0]
            except subprocess.CalledProcessError:
                retcode  = p.poll()
                if retcode != 0 and tries < 10:
                    break
                else:
                    monitor.result = retcode
                    event.set()
                    return
            if newCpuTime > oldCpuTime:
                oldCpuTime = newCpuTime
                event.wait(int(pb_globals.vars['timeout']))
                if event.isSet():
                    log.info("monitor: Caught the quit Event. Killing Subprocess. Please wait...")
                    kill_process_tree(p, parentPid)
                    return
                else: continue
            else:
                log.info("monitor: No CPU Time accumulated. Check for pulse...")
                if cmd[0:4] == "wget":
                    try:
                        newWgetSize = (subprocess.Popen(wgetCheckCmd, shell=True, stdout=subprocess.PIPE).communicate()[0]).strip().split(' ')[0]
                    except subprocess.CalledProcessError:
                        retcode  = p.poll()
                        if retcode != 0 and tries < 10:
                            break
                        else:
                            monitor.result = retcode
                            event.set()
                            return
                    try:
                        if int(newWgetSize) > int(oldWgetSize):
                            oldWgetSize = newWgetSize
                            event.wait(int(pb_globals.vars['timeout']))
                            if event.isSet():
                                log.info("monitor: Caught the quit Event. Killing Subprocess. Please wait...")
                                kill_process_tree(p, parentPid)
                                return
                            else: continue
                    except ValueError: pass
                elif cmd[0:9] == "git clone" or cmd[0:6] == "svn co":
                    try:
                        newGitSize = (subprocess.Popen(gitCheckCmd, shell=True, stdout=subprocess.PIPE).communicate()[0]).strip().split('\t')[0]
                    except subprocess.CalledProcessError:
                        retcode  = p.poll()
                        if retcode != 0 and tries < 10:
                            break
                        else:
                            monitor.result = retcode
                            event.set()
                            return
                    try:
                        if int(newGitSize) > int(oldGitSize):
                            oldGitSize = newGitSize
                            event.wait(int(pb_globals.vars['timeout']))
                            if event.isSet():
                                log.info("monitor: Caught the quit Event. Killing Subprocess. Please wait...")
                                kill_process_tree(p, parentPid)
                                return
                            else: continue
                    except ValueError: pass
                else:
                    try:
                        cpuUsage = (subprocess.Popen(cpuUsageCmd, shell=True, stdout=subprocess.PIPE).communicate()[0]).strip()
                    except subprocess.CalledProcessError:
                        retcode  = p.poll()
                        if retcode != 0 and tries < 10:
                            break
                        else:
                            monitor.result = retcode
                            event.set()
                            return
                    if float(cpuUsage) > 0:
                        event.wait(int(pb_globals.vars['timeout']))
                        if event.isSet():
                            log.info("monitor: Caught the quit Event. Killing Subprocess. Please wait...")
                            kill_process_tree(p, parentPid)
                            return
                        else: continue

                # if we get here, no pulse was detected
                log.info("monitor: No pulse detected!")
                kill_process_tree(p, parentPid)
                if tries < 10:
                    log.info("monitor: Restarting Subprocess...")
                    break
                else:
                    monitor.result = 2
                    event.set()
                    return

    # tried 10 times
    monitor.result = 2
    event.set()
    return

# stdout -> shell
def shellexec_monitor(cmd, throw_ex=True):
    """
    Execute a command on the shell.
    If Ctrl-C is caught, the subprocess will be killed.
    """
    log.debug("shellexec_monitor(): Executing command {}".format(cmd))
    try:
        result = None
        quitEvent = Event()
        monitorThread = Thread(target=monitor, args=(cmd,quitEvent,))
        monitorThread.start()
        while monitorThread.isAlive:
            monitorThread.join(1)
            if quitEvent.isSet():
                log.debug("shellexec_monitor(): Caught the quit Event")
        return monitor.result
    except KeyboardInterrupt:
        log.info("shellexec_monitor(): Caught Ctrl+C. Killing all threads. Patience...")
        quitEvent.set()
        time.sleep(10)
        raise KeyboardInterrupt
    except Exception, e:
        if(throw_ex):
            raise e
        else:
            return -1;

def dict_merge(a, b):
    """
    Recursively merge b into a. b[k] will overwrite a[k] if it exists.
    """
    if not isinstance(b, dict):
        return b
    result = deepcopy(a)
    for k, v in b.iteritems():
        if k in result and isinstance(result[k], dict):
                result[k] = dict_merge(result[k], v)
        else:
            result[k] = deepcopy(v)
    return result

if __name__ == "__main__":
    print get_child_pids(4155)
    kill_process_tree(19735)
