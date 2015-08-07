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
Fetcher. Whoa.
"""

import os

from pybombs import pb_logging
from pybombs import inventory
from pybombs.utils import subproc
from pybombs.utils import output_proc
from pybombs.pb_exception import PBException
from pybombs.config_manager import config_manager
from pybombs.utils import vcompare

from pybombs import fetchers
from pybombs import pb_logging
from pybombs.pb_exception import PBException


class Fetcher(object):
    """
    This will attempt to download source from all the recipe's urls using the avaliable fetchers.
    """

    def __init__(self):
        self.cfg = config_manager
        # Set up logger:
        self.log = pb_logging.logger.getChild("Fetcher")
        self.prefix = self.cfg.get_active_prefix()
        self.src_dir = self.prefix.src_dir
        self.inventory = inventory.Inventory(self.prefix.inv_file)

        if not os.path.isdir(self.src_dir):
            self.log.warning("Source dir does not exist! [{}]".format(self.src_dir))
            try:
                os.mkdir(self.src_dir)
            except:
                raise PBException("Unable to create the source directory!")

        # Get the avaliable fetcher objects.
        self.avaliable = fetchers.get_all()

    def get_url_type(url):
        return url.split("://", 1)[0]

    def fetch(self, recipe):
        """
        Do the fetch. Return version?
        If something goes wrong then throw a PBException
        """
        self.log.debug("Fetching source for recipe: {}".format(recipe.name))

        # Should this be checking the inventory or the src directory?
        """
        if self.check_fetched(recipe, url):
            self.log.info("Already fetched: {}".format(recipe.id))
            return True
        """

        # Jump to the src directory
        cwd = os.getcwd()
        self.log.debug("Switching to src directory: {}".format(self.src_dir))
        os.chdir(self.src_dir)

        # Do the fetch
        fetched = False
        for src in recipe.srcs:
            try:
                # Get the right fetcher
                (url_type, url) = src.split("://", 1)
                fetcher = self.avaliable[url_type]
                self.log.debug("Using fetcher {}".format(fetcher))
                self.log.debug("Fetching {}".format(url))

                # TODO: Use an exception rather than true/false
                if not fetcher._fetch(url, recipe):
                    self.log.warning("Fetching source {0} failed.".format(src))
                    continue
                fetched = True
                break

            except Exception as ex:
                self.log.error("Unable to fetch {}".format(recipe))
                self.log.error(ex)

        # Always switch back
        os.chdir(cwd)

        if not fetched:
            raise PBException("Unable to fetch recipe {}".format(recipe.id))

        # Save status to the inventory
        self.inventory.set_state(recipe.id, self.inventory.STATE_FETCHED)
        self.inventory.save()
        return True

    #TODO: Same as fetch, except wipe out the source directory first
    # Make sure that they don't have path conflicts?
    def refetch(self, recipe):
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

    def check_fetched(self, recipe):
        """
        Check if the recipe was downloaded to the current source directory
        """
        dst_dir = os.path.join(self.src_dir, recipe.id)
        return os.path.isdir(dst_dir)

    def get_version(self, recipe):
        if not self.check_fetched(recipe, url):
            self.log.error("Can't return version for {}, not fetched!".format(recipe.id))
        return None


# Some test code:
if __name__ == "__main__":
    f = Fetcher()
    f.fetch()
    #print pm.exists('gcc')
    #print pm.installed('gcc')
    #print pm.install('gcc')
