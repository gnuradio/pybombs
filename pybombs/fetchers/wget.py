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
wget-style fetcher
"""

import math
import os
import sys
import requests
from pybombs import utils
from pybombs.fetchers.base import FetcherBase

def _download(url):
    """
    Do a wget: Download the file specified in url to the cwd.
    Return the filename.
    """
    filename = os.path.split(url)[1]
    req = requests.get(url, stream=True, headers={'User-Agent': 'PyBOMBS'})
    filesize = float(req.headers.get('content-length', 0))
    filesize_dl = 0
    with open(filename, "wb") as f:
        for buff in req.iter_content(chunk_size=8192):
            if buff:
                f.write(buff)
                filesize_dl += len(buff)
            # TODO wrap this into an output processor or at least
            # standardize the progress bars we use
            if filesize:
                status = r"%05d kB / %05d kB (%03d%%)" % (
                        int(math.ceil(filesize_dl/1000.)),
                        int(math.ceil(filesize/1000.)),
                        int(math.ceil(filesize_dl*100.)/filesize)
                )
            else:
                status = r"%05d kB" % (
                        int(math.ceil(filesize_dl/1000.)),
                )
            status += chr(8)*(len(status)+1)
            sys.stdout.write(status)
    sys.stdout.write("\n")
    return filename

class Wget(FetcherBase):
    """
    Archive downloader fetcher.
    Doesn't actually use wget, name is just for historical reasons.
    """
    url_type = 'wget'
    host_sys_deps = ['python-requests',]
    regexes = [r'https?://.*\.gz$',]

    def __init__(self):
        FetcherBase.__init__(self)

    def fetch_url(self, url, dest, dirname, args=None):
        """
        - src: URL, without the <type>+ prefix.
        - dest: Store the fetched stuff into here
        - dirname: Put the result into a dir with this name, it'll be a subdir of dest
        - args: Additional args to pass to the actual fetcher
        """
        filename = _download(url)
        if utils.is_archive(filename):
            # Move archive contents to the correct source location:
            utils.extract_to(filename, dirname)
            # Remove the archive once it has been extracted:
            os.remove(filename)
        return True

    def update_src(self, src, dest, dirname, args=None):
        """
        For an update, we grab the archive and copy it over into the existing
        directory. Luckily, that's exactly the same as fetch_url().
        """
        return self.fetch_url(src, dest, dirname, args)

    #def get_version(self, recipe, url):
        ## TODO tbw
        #url = recipe.srcs[0]
        #filename = url.split('/')[-1]
        #return None

