#
# Copyright 2015-2017 Free Software Foundation, Inc.
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
git fetcher functions
"""

import os
import re
from pybombs.fetchers.base import FetcherBase
from pybombs.utils import subproc
from pybombs.pb_exception import PBException
from pybombs.utils import vcompare

def parse_git_url(url, args):
    """
    - If a git rev is given in the URL, split that out and put it into the args

    Look for format:
        <URL>@<commit|rev|tag>

    <commit|rev|tag> cannot contain a ':' or whitespace.
    """
    if re.match(r'[a-z]+://[a-z]+@([^@:]+)$', url):
        return url, args
    mobj = re.search(r'(.*)@([^:@]+)$', url)
    if mobj:
        url, args['gitrev'] = mobj.groups()
    return url, args

def get_git_version():
    """
    Return the currently installed git version as a string.
    """
    try:
        return re.search(
            r'[0-9.]+',
            subproc.check_output(['git', '--version'])
        ).group(0)
    except OSError:
        raise PBException("Unable to execute git!")
    except subproc.CalledProcessError:
        raise PBException("Error executing 'git --version'!")
    except AttributeError:
        raise PBException("Unexpected output from 'git --version'!")


class Git(FetcherBase):
    """
    git fetcher
    """
    url_type = 'git'
    host_sys_deps = ['git',]
    regexes = [r'.*\.git$', r'git@',]

    def __init__(self):
        FetcherBase.__init__(self)

    def fetch_url(self, url, dest, dirname, args=None):
        """
        git clone
        """
        git_version = get_git_version()
        self.log.debug("We have git version %s", git_version)
        url, args = parse_git_url(url, args or {})
        self.log.debug("Using url - {0}".format(url))
        git_cmd = ['git', 'clone', url, dirname]
        if args.get('gitargs'):
            for arg in args.get('gitargs').split():
                git_cmd.append(arg)
        if self.cfg.get("git-cache", False):
            from pybombs import gitcache_manager
            gcm = gitcache_manager.GitCacheManager(self.cfg.get("git-cache"))
            self.log.debug("Adding remote into git ref")
            gcm.add_remote(dirname, url, True)
            git_cmd.append(
                '--reference-if-able'
                if vcompare(">=", git_version, "2.11") else '--reference'
            )
            git_cmd.append(self.cfg.get("git-cache"))
        if args.get('gitbranch'):
            git_cmd.append('-b')
            git_cmd.append(args.get('gitbranch'))
        o_proc = None
        subproc.monitor_process(
            args=git_cmd,
            o_proc=o_proc,
            throw_ex=True,
            throw=True,
        )
        # If we have a specific revision, checkout that
        if args.get('gitrev'):
            cwd = os.getcwd()
            src_dir = os.path.join(dest, dirname)
            self.log.trace("Switching cwd to: {0}".format(src_dir))
            os.chdir(src_dir)
            git_co_cmd = ["git", "checkout", "--force", args.get('gitrev')]
            subproc.monitor_process(
                args=git_co_cmd,
                o_proc=o_proc,
                throw_ex=True,
            )
            self.log.trace("Switching cwd to: {0}".format(cwd))
            os.chdir(cwd)
        return True

    def update_src(self, url, dest, dirname, args=None):
        """
        git pull / git checkout
        """
        args = args or {}
        self.log.debug("Using url {0}".format(url))
        cwd = os.getcwd()
        src_dir = os.path.join(dest, dirname)
        self.log.trace("Switching cwd to: {0}".format(src_dir))
        os.chdir(src_dir)
        if args.get('gitrev'):
            # If we have a rev or tag specified, fetch, then checkout.
            git_cmds = [
                ['git', 'fetch', '--tags', '--all', '--prune'],
                ['git', 'checkout', '--force', args.get('gitrev')],
            ]
        elif args.get('gitbranch'):
            # Branch is similar, only we make sure we're up to date
            # with the remote branch
            git_cmds = [
                ['git', 'fetch', '--tags', '--all', '--prune'],
                ['git', 'checkout', '--force', args.get('gitbranch')],
                ['git', 'reset', '--hard', '@{u}'],
            ]
        else:
            # Without a git rev, all we can do is try and pull
            git_cmds = [
                ['git', 'pull', '--rebase'],
            ]
        git_cmds.append(['git', 'submodule', 'update', '--recursive'])
        o_proc = None
        for cmd in git_cmds:
            try:
                if subproc.monitor_process(args=cmd, o_proc=o_proc, throw_ex=True) != 0:
                    self.log.error("Could not run command `{0}`".format(" ".join(cmd)))
                    return False
            except Exception:
                self.log.error("Could not run command `{0}`".format(" ".join(cmd)))
                raise PBException("git commands failed.")
        self.log.trace("Switching cwd back to: {0}".format(cwd))
        os.chdir(cwd)
        return True

