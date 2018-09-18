#
# Copyright 2016 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
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
""" Git cache manager """

from __future__ import print_function
import os
from six import iteritems
from pybombs import pb_logging
from pybombs.utils import sysutils
from pybombs.utils import subproc

class GitCacheManager(object):
    " Git cache manager "
    def __init__(self, path):
        self.path = path
        self.log = pb_logging.logger.getChild("GitCacheManager")
        self.ensure_repo_exists(path)
        self.remotes = self.get_existing_remotes()

    def run_git_command(self, args):
        " Run a git command in path, return to previous cwd, return output "
        git_cmd = ['git'] + args
        cwd = os.getcwd()
        os.chdir(self.path)
        output = subproc.check_output(git_cmd)
        os.chdir(cwd)
        return output

    def ensure_repo_exists(self, path):
        " Guarantee that path is a writable git repo. "
        if not sysutils.dir_is_writable(path):
            self.log.info("Creating new git cache in {path}".format(path=path))
            sysutils.mkdir_writable(path)
            self.run_git_command(['init', '--bare'])

    def get_existing_remotes(self):
        " Return dict remotename->url from current git repo "
        all_remotes = [x.strip() for x in self.run_git_command(['remote']).split()]
        return {
            remote: self.run_git_command(['config', '--get', "remote.%s.url" % remote]).strip()
            for remote in all_remotes
        }

    def add_remote(self, name, url, fetch=False):
        """
        Add a single remote by name and url.
        If fetch is True, will fetch that remote.
        """
        self.log.debug("Adding remote: {name} -> {url}".format(name=name, url=url))
        if url not in self.remotes.values():
            if name in self.remotes:
                self.log.warning(
                    "Trying to add another remote with same name {name}"
                    .format(name=name)
                )
                return
            self.run_git_command(['remote', 'add', name, url])
            self.remotes[name] = url
        else:
            self.log.debug("Remote URL {url} already registered.".format(url=url))
        if fetch:
            self.run_git_command(['remote', 'update', name])

    def add_remotes(self, remotes, fetch=False):
        """
        Fetch all remotes in dict remotes.
        remotes is of format name->url
        If fetch is True, runs fetch --all afterwards.
        """
        for name, url in iteritems(remotes):
            while name in self.remotes:
                name += '_'
            self.add_remote(name, url, False)
        if fetch:
            self.run_git_command(['fetch', '--all', '--prune'])

