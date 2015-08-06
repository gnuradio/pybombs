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
from pybombs.utils import vcompare
from pybombs.fetchers.base import FetcherBase


class File(FetcherBase):
    """
    The 'file://' protocol is a way of saying you have the archive locally.
    Will symlink the file to the source dir and then extract it.
    """
    url_type = 'file'

    def _fetch(self, url, recipe):
        """
        symlink + extract
        """
        filename = os.path.split(url)[-1]
        self.log.debug("Looking for file: {}".format(filename))
        if os.path.isfile(filename):
            self.log.info("File already exists in source dir: {}".format(filename))
            return True
        if not os.path.isfile(url):
            self.log.error("File not found: {}".format(url))
            return False
        if url[0] != "/":
            url = os.path.join("..", url)
        os.symlink(url, os.path.join(self.src_dir, filename))
        utils.extract(filename)

        return True


    def get_version(self, recipe, url):
        if not self.check_fetched(recipe, url):
            self.log.error("Can't return version for {}, not fetched!".format(recipe.id))
            return None
        cwd = os.getcwd()
        repo_dir = os.path.join(self.src_dir, recipe.id)
        self.log.obnoxious("Switching cwd to: {}".format(repo_dir))
        os.chdir(repo_dir)
        # TODO run this process properly
        out1 = subprocess.check_output("svnversion {}".format(repo_dir), shell=True)
        rm = re.search("\d*:*(\d+).*", out1)
        self.version = rm.group(1)
        self.log.debug("Found version: {}".format(self.version))
        self.log.obnoxious("Switching cwd to: {}".format(cwd))
        os.chdir(cwd)
        return self.version
