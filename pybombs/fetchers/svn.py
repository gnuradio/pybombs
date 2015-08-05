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


import os

from pybombs import pb_logging
from pybombs import inventory
from pybombs.utils import subproc
from pybombs.utils import output_proc
from pybombs.pb_exception import PBException
from pybombs.config_manager import config_manager
from pybombs.utils import vcompare
from pybombs.fetchers.base import FetcherBase


class Svn(FetcherBase):
    """
    svn fetcher
    """
    url_type = 'svn'
    def _fetch(self, recipe, url):
        """
        svn checkout
        """

        svn_cmd = "svn co -r {rev} {url} {dst_dir}".format(
                rev=recipe.svn_rev,
                url=url,
                dst_dir=recipe.id
        )
        self.log.debug("Calling '{}'".format(svn_cmd))
        # TODO:
        # - Run the clone process in a process monitor
        # - Pipe its output through an output processor
        if subprocess.call(svn_cmd, shell=True) != 0:
            return False
        return True


    def get_version(self, recipe, url):
        if not self.check_fetched(recipe, url):
            self.log.error("Can't return version for {}, not fetched!".format(recipe.id))
            return None

        repo_dir = os.path.join(self.src_dir, recipe.id)
        self.log.obnoxious("Switching cwd to: {}".format(repo_dir))
        os.chdir(repo_dir)
        # TODO run this process properly
        out1 = subprocess.check_output("svnversion {}".format(repo_dir), shell=True)
        rm = re.search("\d*:*(\d+).*", out1)
        self.version = rm.group(1)
        self.log.debug("Found version: {}".format(self.version))
        self.log.obnoxious("Switching cwd to: {}".format(cwd))

        return self.version
