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
Fetcher: Base class
"""

import re
import os
import copy
import shutil
import subprocess

from pybombs import pb_logging
from pybombs import inventory
from pybombs.utils import subproc
from pybombs.utils import output_proc
from pybombs.pb_exception import PBException
from pybombs.config_manager import config_manager
from pybombs.packagers.base import PackagerBase
from pybombs.utils import vcompare


class FetcherBase(object):
    """
    Base class for fetchers.
    """
    name = None
    url_type = None

    def __init__(self):
        self.cfg = config_manager
        self.log = pb_logging.logger.getChild("Fetcher.{}".format(self.name))
        self.prefix_info = self.cfg.get_active_prefix()
        self.src_dir = self.prefix_info.src_dir

    def fetch(self, recipe, url):
        """
        Do the fetch. If version info is available, return that.
        Only return False or None if something goes wrong.
        """
        self.log.obnoxious("Fetching {} file from url: {}".format(recipe, url))

        # Jump to the src directory (should be created by init?)
        if not os.path.isdir(self.src_dir):
            self.log.error("Source dir does not exist! [{}]".format(self.src_dir))
            return False
        # Should this be checking the inventory or the src directory?
        if self.check_fetched(recipe, url):
            self.log.info("Already fetched: {}".format(recipe.id))
            return True

        cwd = os.getcwd()
        self.log.obnoxious("Switching to src directory: {}".format(self.src_dir))
        os.chdir(self.src_dir)

        # Do the fetch
        try:
            self.log.debug("Fetching {}".format(url))
            self._fetch(recipe, url.split("://", 1)[1])
        except Exception as ex:
            self.log.error("Unable to fetch the {}".format(recipe))
            self.log.error(ex)

        # Always switch
        os.chdir(cwd)
        return True

    def _fetch(self, recipe, url):
        """
        Overload this to implement the actual fetch.
        """
        raise RuntimeError("Can't fetch {} from {} -- Function not implemented!".format(recipe.id, url))

    def refetch(self, recipe, url):
        """
        Do a fetch even though already fetched. Default behaviour is to kill
        the dir and do a new fetch. Returns the fetch result.
        """
        dst_dir = os.path.join(self.src_dir, recipe.id)
        if os.path.isdir(dst_dir):
            self.log.debug("refetch(): Found existing directory {}. Nuking that.".format(dst_dir))
            shutil.rmtree(dst_dir, ignore_errors=True)
            if os.path.isdir(dst_dir):
                raise PBException("Can't nuke existing directory {}".format(dst_dir))
            # TODO We should update the inventory here
        return self.fetch(recipe, url)

    def check_fetched(self, recipe, url):
        """
        Check if the recipe was downloaded to the current source directory
        """
        dst_dir = os.path.join(self.src_dir, recipe.id)
        return os.path.isdir(dst_dir)

    def get_version(self, recipe, url):
        if not self.check_fetched(recipe, url):
            self.log.error("Can't return version for {}, not fetched!".format(recipe.id))
        return None


### Factory functions #######################################################
def get_fetcher_dict():
    """
    Return list of Fetchers
    """
    fetcher_dict = {}
    from pybombs import fetchers
    for g in fetchers.__dict__.values():
        try:
            if issubclass(g, FetcherBase) and g.url_type is not None:
                fetcher_dict[g.url_type] = g
                print ("Added fetcher type {}".format(g.url_type))
        except (TypeError, AttributeError):
            pass
    return fetcher_dict
    """
    for g in objs:
        try:
            if issubclass(g, PackagerBase) and g.name == name:
                return g()
        except (TypeError, AttributeError):
            pass
    return None
    """

def get_url_type(url):
    return url.split("://", 1)[0]

def make_fetcher(recipe, url):
    """ Fetcher Factory """
    fetcher_dict = get_fetcher_dict()
    url_type = get_url_type(url)
    return fetcher_dict[url_type]()
