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
from pybombs.pb_exception import PBException
from pybombs.config_manager import config_manager


class FetcherBase(object):
    """
    Base class for fetchers.
    """
    url_type = None

    def __init__(self):
        self.cfg = config_manager
        self.log = pb_logging.logger.getChild("Fetcher.{}".format(self.url_type))

    def _fetch(self, url, recipe):
        """
        Overload this to implement the actual fetch.
        """
        raise RuntimeError("Can't fetch {} -- Function not implemented!".format(url))

    def _clean(self):
        """
        Overload this to implement the actual fetch.
        """
        raise RuntimeError("Can't clean -- Function not implemented!")


# Factory functions
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
