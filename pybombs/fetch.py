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
fetcher
"""

import re
import os
import shutil
import subprocess

from pb_exception import PBException
import pb_logging
import config_manager

class Fetcher(object):
    """
    Fetcher Base class.
    """
    url_type = None
    def __init__(self):
        self.log = pb_logging.logger.getChild("Fetcher.{}".format(self.url_type))
        self.cfg = config_manager.config_manager
        self.prefix_info = self.cfg.get_active_prefix()
        self.src_dir = self.prefix_info.src_dir

    def fetch(self, recipe):
        """
        Do the fetch
        """
        if self.check_fetched(recipe):
            self.log.info("Already fetched: {}".format(recipe.id))
            return True
        url = recipe.srcs[0]
        return self._fetch(recipe, url.split("://", 1)[1])

    def _fetch(self, recipe, url):
        """
        Overload this to implement the actual fetch.
        """
        raise RuntimeError("Can't fetch {} from {} -- Function not implemented!".format(recipe.id, url))


    def refetch(self, recipe):
        """
        Do a fetch even though already fetched. Default behaviour is to kill
        the dir and do a new fetch.
        """
        dst_dir = os.path.join(self.src_dir, recipe.id)
        if os.path.isdir(dst_dir):
            self.log.debug("refetch(): Found existing directory {}. Nuking that.".format(dst_dir))
            shutil.rmtree(dst_dir, ignore_errors=True)
            if os.path.isdir(dst_dir):
                raise PBException("Can't nuke existing directory {}".format(dst_dir))
        self.fetch(recipe)

    def check_fetched(self, recipe):
        """
        Check if the recipe was downloaded to the current source directory
        """
        dst_dir = os.path.join(self.src_dir, recipe.id)
        return os.path.isdir(dst_dir)

    def get_version(self, recipe):
        if not self.check_fetched(recipe):
            raise PBException("Can't return version for {}, not fetched!".format(recipe.id))
        return None



class FetcherGit(Fetcher):
    """
    git fetcher
    """
    url_type = 'git'
    def _fetch(self, recipe, url):
        """
        git clone (or git pull TODO)
        """
        self.log.debug("Fetching {}".format(url))
        cwd = os.getcwd()
        os.chdir(self.src_dir)
        self.log.obnoxious("Switching cwd to: {}".format(self.src_dir))
        gitcache = self.cfg.get("git-cache", "")
        if gitcache is not "":
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
        self.log.debug("Calling {}".format(git_cmd))
        # TODO:
        # - Run the clone process in a process monitor
        # - Pipe its output through an output processor
        if subprocess.call(git_cmd, shell=True) != 0:
            return False
        self.log.obnoxious("Switching cwd to: {}".format(os.path.join(self.src_dir, recipe.id)))
        os.chdir(os.path.join(self.src_dir, recipe.id))
        if recipe.git_rev:
            git_co_cmd = "git checkout {rev}".format(recipe.git_rev)
            self.log.debug("Calling {}".format(git_co_cmd))
            # TODO:
            # - Run the clone process in a process monitor
            # - Pipe its output through an output processor
            if subprocess.call(git_co_cmd, shell=True) != 0:
               return False
        self.log.obnoxious("Switching cwd to: {}".format(cwd))
        os.chdir(cwd)
        return True

    def get_version(self, recipe):
        if not self.check_fetched(recipe):
            raise PBException("Can't return version for {}, not fetched!".format(recipe.id))
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


### Factory functions #######################################################
def get_fetcher_dict():
    """
    Return list of Fetchers
    """
    fetcher_dict = {}
    for g in globals().values():
        try:
            if issubclass(g, Fetcher) and g.url_type is not None:
                fetcher_dict[g.url_type] = g
        except (TypeError, AttributeError):
            pass
    return fetcher_dict

def get_url_type_from_recipe(recipe):
    url = recipe.srcs[0]
    return url.split("://", 1)[0]

def make_fetcher(recipe):
    """ Fetcher Factory """
    fetcher_dict = get_fetcher_dict()
    url_type = get_url_type_from_recipe(recipe)
    return fetcher_dict[url_type]()

#def fetch(recipe):
    #url = recipe.srcs[0]
    #url_type, url = url.split("://", 1)
    #fetcher = make_fetcher(url_type)
    #return fetcher.fetch(recipe, url)


#if __name__ == "__main__":

