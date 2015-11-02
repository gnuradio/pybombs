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
svn fetcher
"""

import os
from pybombs.utils import subproc
from pybombs.fetchers.base import FetcherBase

class Svn(FetcherBase):
    """
    svn fetcher
    """
    url_type = 'svn'
    # TODO: add svn dependency
    #host_sys_deps = ['svn',]

    def __init__(self):
        FetcherBase.__init__(self)

    def fetch_url(self, url, dest, dirname, args=None):
        """
        - url: SVN repo url
        - dest: src dir
        - dirname: Put the result into a dir with this name, it'll be a subdir of dest
        - args: Additional args to pass to the actual fetcher
        """
        args = args or {}
        svn_cmd = ['svn', 'co']
        if args.get('svnrev') is not None:
            svn_cmd.append('-r')
            svn_cmd.append(args.get('svnrev'))
        svn_cmd.append(url)
        svn_cmd.append(dirname)
        subproc.monitor_process(
            args=svn_cmd,
            #o_proc=foo, # FIXME
            throw_ex=True,
        )
        return True

    def update_src(self, url, dest, dirname, args=None):
        """
        - src: URL, without the <type>+ prefix.
        - dest: Store the fetched stuff into here
        - dirname: Put the result into a dir with this name, it'll be a subdir of dest
        - args: Additional args to pass to the actual fetcher
        """
        args = args or {}
        self.log.debug("Using url {0}".format(url))
        cwd = os.getcwd()
        src_dir = os.path.join(dest, dirname)
        self.log.obnoxious("Switching cwd to: {}".format(src_dir))
        os.chdir(src_dir)
        svn_cmd = ['svn', 'up', '--force']
        if args.get('svnrev'):
            svn_cmd.append('--revision')
            svn_cmd.append(args.get('svnrev'))
        subproc.monitor_process(
            args=svn_cmd,
            throw_ex=True,
            #o_proc=foo #FIXME
        )
        self.log.obnoxious("Switching cwd back to: {0}".format(cwd))
        os.chdir(cwd)
        return True

    #def get_version(self, recipe, url):
        #if not self.check_fetched(recipe, url):
            #self.log.error("Can't return version for {}, not fetched!".format(recipe.id))
            #return None

        #repo_dir = os.path.join(self.src_dir, recipe.id)
        #self.log.obnoxious("Switching cwd to: {}".format(repo_dir))
        #os.chdir(repo_dir)
        ## TODO run this process properly
        #out1 = subprocess.check_output("svnversion {}".format(repo_dir), shell=True)
        #rm = re.search("\d*:*(\d+).*", out1)
        #self.version = rm.group(1)
        #self.log.debug("Found version: {}".format(self.version))
        #self.log.obnoxious("Switching cwd to: {}".format(cwd))
        #return self.version
