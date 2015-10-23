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
git fetcher functions
"""

import os
import subprocess
from pybombs.fetchers.base import FetcherBase

class Git(FetcherBase):
    """
    git fetcher
    """
    url_type = 'git'

    def fetch_url(self, url, dest, dirname, args={}):
        """
        git clone
        """
        self.log.debug("Using url - {}".format(url))
        gitcache = self.cfg.get("git-cache", "")
        if len(gitcache): # Check if this is a directory
            self.log.debug("Using gitcache at {}", gitcache)
            gitcache = " --reference {}".format(gitcache)
        git_cmd = "git clone {gitargs}{gitcache} -b {branch} {url} {name}".format(
            gitargs=args.get('gitargs', ''),
            gitcache=gitcache,
            branch=args.get('gitbranch', ''),
            url=url,
            name=dirname,
        )
        self.log.debug("Calling '{0}'".format(git_cmd))
        # TODO:
        # - Run the clone process in a process monitor
        # - Pipe its output through an output processor
        if subprocess.call(git_cmd, shell=True) != 0:
            return False
        # Jump to the cloned repo
        # We are already in the source directory for the prefix
        cwd = os.getcwd()
        src_dir = os.path.join(dest, dirname)
        self.log.obnoxious("Switching cwd to: {}".format(src_dir))
        os.chdir(src_dir)
        if args.get('gitrev'):
            git_co_cmd = "git checkout {rev}".format(args.get('gitrev'))
            self.log.debug("Calling '{}'".format(git_co_cmd))
            # TODO:
            # - Run the clone process in a process monitor
            # - Pipe its output through an output processor
            if subprocess.call(git_co_cmd, shell=True) != 0:
                return False
        self.log.obnoxious("Switching cwd to: {}".format(cwd))
        os.chdir(cwd)
        return True

    def update_src(self, url, dest, dirname, args={}):
        """
        git pull
        """
        assert False
        self.log.debug("Using url - {}".format(url))
        cwd = os.getcwd()
        os.chdir(os.path.join(dest, dirname))
        gitcache = self.cfg.get("git-cache", "")
        if len(gitcache): # Check if this is a directory
            self.log.debug("Using gitcache at {}", gitcache)
            gitcache = " --reference {}".format(gitcache)
        git_cmd = "git clone {gitargs}{gitcache} -b {branch} {url} {name}".format(
            gitargs=args.get('gitargs', ''),
            gitcache=gitcache,
            branch=args.get('gitbranch', ''),
            url=url,
            name=dirname,
        )
        self.log.debug("Calling '{}'".format(git_cmd))
        # TODO:
        # - Run the clone process in a process monitor
        # - Pipe its output through an output processor
        if subprocess.call(git_cmd, shell=True) != 0:
            return False
        # Jump to the cloned repo
        # We are already in the source directory for the prefix
        src_dir = os.path.join(dest, dirname)
        self.log.obnoxious("Switching cwd to: {}".format(src_dir))
        if args.get('gitrev'):
            git_co_cmd = "git checkout {rev}".format(args.get('gitrev'))
            self.log.debug("Calling '{}'".format(git_co_cmd))
            # TODO:
            # - Run the clone process in a process monitor
            # - Pipe its output through an output processor
            if subprocess.call(git_co_cmd, shell=True) != 0:
                return False
        self.log.obnoxious("Switching cwd to: {}".format(cwd))
        os.chdir(cwd)
        return True

    #def get_version(self, recipe, url):
        #if not self.check_fetched(recipe, url):
            #self.log.error("Can't return version for {}, not fetched!".format(recipe.id))
            #return None
        #cwd = os.getcwd()
        #self.log.obnoxious("Switching cwd to: {}".format(os.path.join(self.src_dir, recipe.id)))
        #os.chdir(os.path.join(self.src_dir, recipe.id))
        ## TODO run this process properly
        #out1 = subprocess.check_output("git rev-parse HEAD", shell=True)
        #rm = re.search("([0-9a-f]+).*", out1)
        #self.version = rm.group(1)
        #self.log.debug("Found version: {}".format(self.version))
        #self.log.obnoxious("Switching cwd to: {}".format(cwd))
        #os.chdir(cwd)
        #return self.version

