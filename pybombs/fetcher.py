#!/usr/bin/env python
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
import re
import shutil

from pybombs import pb_logging
from pybombs.pb_exception import PBException
from pybombs.config_manager import config_manager

class Fetcher(object):
    """
    This will attempt to download source from all the recipe's urls using the available fetchers.
    """
    def __init__(self):
        self.cfg = config_manager
        self.log = pb_logging.logger.getChild("Fetcher")
        self.prefix = self.cfg.get_active_prefix()
        if self.prefix.prefix_dir is not None:
            self.inventory = self.prefix.inventory
            self.src_dir = self.prefix.src_dir
        from pybombs import fetchers
        self.available = fetchers.get_all()

    def get_fetcher(self, src):
        """
        Return scrubbed URL and fetcher for src.
        """
        (url_type, url) = self.parse_uri(src)
        self.log.debug("Getting fetcher for {url}, type {t}".format(url=url, t=url_type))
        fetcher = self.available.get(url_type)
        if not fetcher:
            raise PBException("No fetcher for type {t}".format(t=url_type))
        self.log.debug("Using fetcher {}".format(fetcher))
        return (fetcher, url)

    def fetch_url(self, src, dest, dirname, args=None):
        """
        - src: Source URL
        - dest: Store the fetched stuff into here
        - dirname: Put the result into a dir with this name, it'll be a subdir of dest
        - args: Additional args to pass to the actual fetcher
        """
        (fetcher, url) = self.get_fetcher(src)
        cwd = os.getcwd()
        if not os.path.isdir(dest):
            os.mkdir(dest)
        os.chdir(dest)
        fetcher.assert_requirements()
        result = fetcher.fetch_url(url, dest, dirname, args)
        os.chdir(cwd)
        return result

    def update_src(self, src, dest, dirname, args=None):
        """
        - src: Source URL
        - dest: Store the fetched stuff into here
        - dirname: Update the result inside a dir with this name, it'll be a subdir of dest
        - args: Additional args to pass to the actual fetcher
        """
        (fetcher, url) = self.get_fetcher(src)
        cwd = os.getcwd()
        os.chdir(dest)
        fetcher.assert_requirements()
        result = fetcher.update_src(url, dest, dirname, args)
        os.chdir(cwd)
        return result

    def fetch(self, recipe):
        """
        Fetch a package identified by its recipe into the current prefix.
        If a package was already fetched, do nothing.

        Contract:
        - Will either raise PBException or the fetch was successful.
        """
        self.log.debug("Fetching source for recipe: {0}".format(recipe.id))
        if self.check_fetched(recipe):
            self.log.info("Already fetched: {0}".format(recipe.id))
            return True
        # Jump to the src directory
        cwd = os.getcwd()
        self.log.debug("Switching to src directory: {0}".format(self.src_dir))
        if not os.path.isdir(self.src_dir):
            os.mkdir(self.src_dir)
        os.chdir(self.src_dir)
        if os.path.exists(os.path.join(self.src_dir, recipe.id)):
            raise PBException(
                "Directory {d} already exists!".format(d=os.path.join(self.src_dir, recipe.id))
            )
        # Do the fetch
        for src in recipe.source:
            src = recipe.var_replace_all(src)
            self.log.obnoxious("Trying to fetch {0}".format(src))
            try:
                if self.fetch_url(src, self.src_dir, recipe.id, recipe.get_dict()):
                    self.log.obnoxious("Success.")
                    self.inventory.set_key(recipe.id, 'source', src)
                    if self.inventory.get_state(recipe.id) < self.inventory.STATE_FETCHED:
                        self.inventory.set_state(recipe.id, self.inventory.STATE_FETCHED)
                    self.inventory.save()
                    os.chdir(cwd)
                    return True
            except PBException as ex:
                self.log.debug("That didn't work.")
                self.log.debug(str(ex))
            except Exception as ex:
                self.log.error("Unexpected error while fetching {0}.".format(src))
                self.log.error(ex)
        # Ideally, we've left the function at this point.
        raise PBException("Unable to fetch recipe {0}".format(recipe.id))

    def refetch(self, recipe):
        """
        Do a fetch even though already fetched. Default behaviour is to kill
        the dir and do a new fetch. Returns the fetch result.
        Note this usually nukes the build directory, too.
        """
        dst_dir = os.path.join(self.src_dir, recipe.id)
        if os.path.isdir(dst_dir):
            self.log.debug("refetch(): Found existing directory {}. Nuking that.".format(dst_dir))
            shutil.rmtree(dst_dir, ignore_errors=True)
            if os.path.isdir(dst_dir):
                raise PBException("Can't nuke existing directory {}".format(dst_dir))
        res = self.fetch(recipe)
        if res:
            # Fetch may not set state to fetched, but here we have to.
            self.inventory.set_state(recipe.id, self.inventory.STATE_FETCHED)
            self.inventory.save()
        return res

    def update(self, recipe):
        """
        Try to softly update the source directory.
        This means the build dir might actually survive.
        """
        self.log.debug("Updating source for recipe: {0}".format(recipe.id))
        if not self.check_fetched(recipe):
            self.log.error("Cannot update recipe {r}, it is not yet fetched.".format(r=recipe.id))
            return False
        # Jump to the src directory
        cwd = os.getcwd()
        self.log.debug("Switching to src directory: {0}".format(self.src_dir))
        os.chdir(self.src_dir)
        if not os.path.isdir(os.path.join(self.src_dir, recipe.id)):
            raise PBException("Source directory {d} does not exist!!".format(
                d=os.path.join(self.src_dir, recipe.id)
            ))
        # Figure out which source was used before
        src = self.inventory.get_key(recipe.id, 'source')
        if not src:
            raise PBException("Cannot establish prior source for package {p}".format(p=recipe.id))
        # Do the update
        self.log.obnoxious("Trying to update from {0}".format(src))
        try:
            if self.update_src(src, self.src_dir, recipe.id, recipe.get_dict()):
                self.log.obnoxious("Update successful.")
                if self.inventory.get_state(recipe.id) >= self.inventory.STATE_CONFIGURED:
                    self.log.obnoxious("Setting package state to 'configured'.")
                    self.inventory.set_state(recipe.id, self.inventory.STATE_CONFIGURED)
                else:
                    self.log.obnoxious("Setting package state to 'fetched'.")
                    self.inventory.set_state(recipe.id, self.inventory.STATE_FETCHED)
                self.inventory.save()
                os.chdir(cwd)
                self.log.obnoxious("Update completed.")
                return True
        except PBException as ex:
            self.log.debug("That didn't work.")
            self.log.debug(str(ex))
        except Exception as ex:
            self.log.error("Unexpected error while fetching {0}.".format(src))
            self.log.error(ex)
        # Ideally, we've left the function at this point.
        raise PBException("Unable to update recipe {0}".format(recipe.id))

    def check_fetched(self, recipe):
        """
        Check if the recipe was downloaded to the current source directory
        # Should this be checking the inventory or the src directory?
        # Or both?
        """
        dst_dir = os.path.join(self.src_dir, recipe.id)
        return os.path.isdir(dst_dir)

    def get_version(self, recipe):
        """
        FIXME TODO fix
        """
        # FIXME TODO fix
        if not self.check_fetched(recipe):
            self.log.error("Can't return version for {}, not fetched!".format(recipe.id))
        return None

    def parse_uri(self, uri):
        """
        Return a tuple (url_type, url).
        """
        url = None
        # If we're lucky, it starts with git+... or whatever
        url_type = uri.split('+', 1)[0]
        uri_types = self.available.keys()
        if url_type in uri_types:
            url = uri[len(url_type)+1:]
            return (url_type, url)
        # OK, let's try and identify it.
        try: # Is it a file?
            os.stat(uri)
            return ('file', uri)
        except OSError:
            pass
        # No, OK, let's try regexing this guy
        for utype in uri_types:
            for regex in self.available[utype].regexes:
                if re.match(regex, uri):
                    return (utype, uri)
        # Yeah, whatever, I give up.
        raise PBException("Unrecognized URI: {uri}".format(uri=uri))

