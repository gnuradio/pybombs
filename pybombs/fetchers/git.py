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


class Git(FetcherBase):
    """
    git fetcher
    """
    url_type = 'git'

    def _fetch(self, url, recipe):
        """
        git clone (or git pull TODO)
        """

        self.log.debug("Using url - {}".format(url))
        gitcache = self.cfg.get("git-cache", "")
        if len(gitcache):
            self.log.debug("Using gitcache at {}", gitcache)
            gitcache = "--reference {}".format(gitcache)
        # TODO maybe we don't want depth=1, ask config_manager
        git_args = "--depth=1"
        git_cmd = "git clone {recipe_gitargs} {gitargs} {gitcache} -b {branch} {url} {name}".format(
            recipe_gitargs=recipe.git_args,
            gitargs=git_args,
            gitcache=gitcache,
            branch=recipe.git_branch,
            url=url,
            name=recipe.id
        )
        self.log.debug("Calling '{}'".format(git_cmd))
        # TODO:
        # - Run the clone process in a process monitor
        # - Pipe its output through an output processor
        if subprocess.call(git_cmd, shell=True) != 0:
            return False
        self.log.obnoxious("Switching cwd to: {}".format(os.path.join(self.src_dir, recipe.id)))
        os.chdir(os.path.join(self.src_dir, recipe.id))
        if recipe.git_rev:
            git_co_cmd = "git checkout {rev}".format(recipe.git_rev)
            self.log.debug("Calling '{}'".format(git_co_cmd))
            # TODO:
            # - Run the clone process in a process monitor
            # - Pipe its output through an output processor
            if subprocess.call(git_co_cmd, shell=True) != 0:
                return False
        self.log.obnoxious("Switching cwd to: {}".format(cwd))
        return True

    def get_version(self, recipe, url):
        if not self.check_fetched(recipe, url):
            self.log.error("Can't return version for {}, not fetched!".format(recipe.id))
            return None
        cwd = os.getcwd()
        self.log.obnoxious("Switching cwd to: {}".format(os.path.join(self.src_dir, recipe.id)))
        os.chdir(os.path.join(self.src_dir, recipe.id))
        # TODO run this process properly
        out1 = subprocess.check_output("git rev-parse HEAD", shell=True)
        rm = re.search("([0-9a-f]+).*", out1)
        self.version = rm.group(1)
        self.log.debug("Found version: {}".format(self.version))
        self.log.obnoxious("Switching cwd to: {}".format(cwd))
        os.chdir(cwd)
        return self.version
