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
'file' pseudo-fetcher
"""

import os
from pybombs import utils
from pybombs.fetchers.base import FetcherBase

class File(FetcherBase):
    """
    The 'file' protocol is a way of saying you have the archive locally.
    Will symlink the file to the source dir and then extract it if its an archive.
    """
    url_type = 'file'

    def __init__(self):
        FetcherBase.__init__(self)

    def fetch_url(self, url, dest, dirname, args=None):
        """
        - url: File we'll link in.
        - dest: Store the fetched stuff into here
        - dirname: Put the result into a dir with this name, it'll be a subdir of dest
        - args: Additional args to pass to the actual fetcher
        """
        if not os.path.isfile(url):
            self.log.error("File not found: {0}".format(url))
            return False
        filename = os.path.split(url)[-1]
        self.log.debug("Looking for file: {0}".format(filename))
        if os.path.isfile(filename):
            self.log.info("File already exists in source dir: {0}".format(filename))
        else:
            self.log.debug("Symlinking file to source dir.")
            os.symlink(url, os.path.join(os.getcwd(), filename))
        if args.has_key("md5"):
            self.log.debug("Calculating MD5 sum for {0}...".format(filename))
            actual_md5 = utils.md5sum(filename)
            if actual_md5 != args["md5"]:
                self.log.error("MD5 sums do not match!")
                return False
        if utils.is_archive(filename):
            self.log.debug("Unpacking {ar}".format(ar=filename))
            # Move to the correct source location.
            utils.extract_to(filename, dirname)
            # Remove the archive once it has been extracted
            os.remove(filename)
        return True

    def update_src(self, url, dest, dirname, args=None):
        """
        - src: URL, without the <type>+ prefix.
        - dest: Store the fetched stuff into here
        - dirname: Put the result into a dir with this name, it'll be a subdir of dest
        - args: Additional args to pass to the actual fetcher
        """
        filename = os.path.split(url)[-1]
        if os.path.isfile(filename):
            os.remove(filename)
        return self.fetch_url(url, dest, dirname, args)

