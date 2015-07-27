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


class Wget(FetcherBase):
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
        os.chdir(cwd)
        return True

    def get_version(self, recipe, url):
        # TODO tbw
        url = recipe.srcs[0]
        filename = url.split('/')[-1]
        return None
