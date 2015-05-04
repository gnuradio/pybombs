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

    def fetch(self, recipe, url):
        """
        Do the fetch
        """
        if self.check_fetched(recipe, url):
            self.log.info("Already fetched: {}".format(recipe.id))
            return True
        self.log.debug("Fetching {}".format(url))
        return self._fetch(recipe, url.split("://", 1)[1])

    def _fetch(self, recipe, url):
        """
        Overload this to implement the actual fetch.
        """
        raise RuntimeError("Can't fetch {} from {} -- Function not implemented!".format(recipe.id, url))


    def refetch(self, recipe, url):
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



### Git #####################################################################
class FetcherGit(Fetcher):
    """
    git fetcher
    """
    url_type = 'git'
    def _fetch(self, recipe, url):
        """
        git clone (or git pull TODO)
        """
        cwd = os.getcwd()
        os.chdir(self.src_dir)
        self.log.obnoxious("Switching cwd to: {}".format(self.src_dir))
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
            os.chdir(cwd)
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
                os.chdir(cwd)
                return False
        self.log.obnoxious("Switching cwd to: {}".format(cwd))
        os.chdir(cwd)
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

### SVN #####################################################################
class FetcherSVN(Fetcher):
    """
    svn fetcher
    """
    url_type = 'svn'
    def _fetch(self, recipe, url):
        """
        svn checkout
        """
        cwd = os.getcwd()
        self.log.obnoxious("Switching cwd to: {}".format(self.src_dir))
        os.chdir(self.src_dir)
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
            os.chdir(cwd)
            return False
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

### File ####################################################################
class FetcherFile(Fetcher):
    """
    The 'file://' protocol is a way of saying you have the archive locally.
    Will symlink the file to the source dir and then extract it.
    """
    url_type = 'file'
    def _fetch(self, recipe, url):
        """
        symlink + extract
        """
        cwd = os.getcwd()
        self.log.obnoxious("Switching cwd to: {}".format(self.src_dir))
        os.chdir(self.src_dir)
        fname = os.path.split(url)[-1]
        if os.path.isfile(fname):
            self.log.info("File already exists in source dir: {}".format(fname))
            return True
        if not os.path.isfile(url):
            self.log.error("File not found: {}".format(url))
            return False
        if url[0] != "/":
            url = os.path.join("..", url)
        os.symlink(url, os.path.join(self.src_dir, fname))
        utils.extract(fname)
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

### wget ####################################################################
class FetcherWget(Fetcher):
    """
    Archive downloader fetcher.
    Doesn't actually use wget, name is just for historical reasons.
    """
    url_type = 'wget'
    def _fetch(self, recipe, url):
        """
        do download
        """
        cwd = os.getcwd()
        self.log.obnoxious("Switching cwd to: {}".format(self.src_dir))
        os.chdir(self.src_dir)
        fname = os.path.split(url)[1]
        # Inspired by http://stackoverflow.com/questions/22676/how-do-i-download-a-file-over-http-using-python
        import urllib2
        filename = url.split('/')[-1]
        u = urllib2.urlopen(url)
        f = open(filename, 'wb')
        meta = u.info()
        file_size = int(meta.getheaders("Content-Length")[0])
        print "Downloading: %s Bytes: %s" % (filename, file_size)
        file_size_dl = 0
        block_sz = 8192
        while True:
            buffer = u.read(block_sz)
            if not buffer:
                break
            file_size_dl += len(buffer)
            f.write(buffer)
            status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
            status = status + chr(8)*(len(status)+1)
            print status,
        f.close()
        utils.extract(filename)
        return True

    def get_version(self, recipe, url):
        # TODO tbw
        url = recipe.srcs[0]
        filename = url.split('/')[-1]
        return None

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

def get_url_type(url):
    return url.split("://", 1)[0]

def make_fetcher(recipe, url):
    """ Fetcher Factory """
    fetcher_dict = get_fetcher_dict()
    url_type = get_url_type(url)
    return fetcher_dict[url_type]()

