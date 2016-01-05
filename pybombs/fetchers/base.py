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

from pybombs import pb_logging
from pybombs.config_manager import config_manager
from pybombs.requirer import Requirer

class FetcherBase(Requirer):
    """
    Base class for fetchers.
    """
    url_type = None
    regexes = []

    def __init__(self):
        Requirer.__init__(self)
        self.cfg = config_manager
        self.log = pb_logging.logger.getChild("Fetcher.{}".format(self.url_type))

    def fetch_url(self, url, dest, dirname, args=None):
        """
        Do an initial fetch of `url' into directory `dest/dirname'.

        - src: URL, without the <type>+ prefix.
        - dest: Store the fetched stuff into here
        - dirname: Put the result into a dir with this name, it'll be a subdir of dest
        - args: Additional args to pass to the actual fetcher
        """
        raise NotImplementedError

    def update_src(self, url, dest, dirname, args=None):
        """
        Update a previously fetched source. It must be located in
        `dest/dirname`, and it must have been fetched using `url'.

        - src: URL, without the <type>+ prefix.
        - dest: Store the fetched stuff into here
        - dirname: Put the result into a dir with this name, it'll be a subdir of dest
        - args: Additional args to pass to the actual fetcher
        """
        raise NotImplementedError

### Factory functions #######################################################
def get_all():
    """
    Return dictionary of Fetchers
    """
    fetcher_dict = {}
    from pybombs import fetchers
    for g in fetchers.__dict__.values():
        try:
            if issubclass(g, FetcherBase) and g.url_type is not None:
                fetcher_dict[g.url_type] = g()
        except (TypeError, AttributeError):
            pass
    return fetcher_dict

def get_by_name(url_type):
    """
    Return fetcher for specific url type
    """
    from pybombs import fetchers
    for g in fetchers.__dict__.values():
        try:
            if issubclass(g, FetcherBase) and g.url_type == url_type:
                return g()
        except (TypeError, AttributeError):
            pass

