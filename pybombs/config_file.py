#
# Copyright 2016 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
#
# GNU Radio is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# GNU Radio is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GNU Radio; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#
""" Abstraction for config files """

import os
from collections import OrderedDict
from ruamel import yaml
from pybombs.utils import dict_merge
from pybombs.pb_exception import PBException
from pybombs.utils import sysutils


def touch_file(filename):
    """
    Like mkdir -p && touch
    """
    sysutils.mkdirp_writable(os.path.dirname(filename))
    if not os.path.exists(filename):
        open(filename, 'a').close()

class AbstractYaml(object):
    """
    Abstraction layer around yaml, so we can do round_trip_* regardless of the
    YAML version.
    """
    def __init__(self):
        if yaml.version_info >= (0, 15):
            self.yaml = yaml.YAML(typ='rt')
            self.yaml.default_flow_style = False
            self._load = self.yaml.load
            self._dump = self.yaml.dump
        else:
            raise AssertionError("Invalid ruamel.yaml version")

    def load(self, fd):
        """Load contents of a file descriptor and return a dictionary."""
        return self._load(fd)

    def dump(self, data, out):
        """Dump contents of a dictionary"""
        return self._dump(data, out)



class PBConfigFile(object):
    """
    Abstraction layer for our config and other files
    """
    def __init__(self, filename):
        # Store normalized path, in case someone chdirs after calling the ctor
        self._filename = os.path.abspath(os.path.expanduser(os.path.normpath(filename)))
        self.data = None
        self.yaml = AbstractYaml()
        touch_file(filename)
        with open(filename) as fn:
            try:
                # TODO: Recursively turn this into an OrderedDict, not just at
                # top level. In a nested dict, some key elements will still be
                # ruamel.ordereddict.
                self.data = OrderedDict(self.yaml.load(fn.read()) or {})
            except (IOError, OSError):
                self.data = OrderedDict()
            except Exception as e:
                raise PBException("Error loading {0}: {1}".format(filename, str(e)))
        assert isinstance(self.data, OrderedDict)

    def get(self, key=None, default=None):
        " Return the data from the config file as a dict "
        if key is None:
            return self.data
        if default is None:
            default = OrderedDict()
        # TODO Again, this is not recursive and sub-values may be non-vanilla
        # ordered dicts
        return OrderedDict(self.data.get(key, default))

    def save(self, newdata=None):
        " Write the contents of the data cache to the file. "
        if newdata is not None:
            assert isinstance(newdata, dict)
            self.data = newdata
        fpath = os.path.split(self._filename)[0]
        if len(fpath):
            sysutils.mkdirp_writable(fpath)
        with open(self._filename, 'w') as fn:
            self.yaml.dump(self.data, fn)

    def update(self, newdata):
        " Overwrite the data with newdata recursively. Updates the file. "
        self.data = dict_merge(self.data, newdata)
        self.save()
        return self.data
