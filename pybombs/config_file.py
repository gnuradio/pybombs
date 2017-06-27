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
import errno
from ruamel import yaml
from pybombs.utils import dict_merge
from pybombs.pb_exception import PBException
from pybombs.utils import sysutils


def touchFile(filename):
    #https://stackoverflow.com/questions/12517451/automatically-creating-directories-with-file-output
    if not os.path.exists(os.path.dirname(filename)):
        try:
            os.makedirs(os.path.dirname(filename))

        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise
    if not os.path.exists(filename):
        open(filename, 'a').close()

class abstractYaml(object):
    def __init__(self):
        if yaml.version_info >= (0,15):
            self.yaml = yaml.YAML(typ='rt')
            self.yaml.default_flow_style=False
            self._load = self.yaml.load
            self._dump = self.yaml.dump
        else:
            self.yaml = yaml
            self._load = self.yaml.round_trip_load
            self._dump = self.yaml.round_trip_dump

    def load(self, fd):
        return self._load(fd)

    def dump(self, data, out):
        if yaml.version_info >= (0,15):
            return self._dump(data, out)
        else:
            return self._dump(data, out, default_flow_style=False)




class PBConfigFile(object):
    """
    Abstraction layer for our config and other files
    """
    def __init__(self, filename):
        # Store normalized path, in case someone chdirs after calling the ctor
        self._filename = os.path.abspath(os.path.expanduser(os.path.normpath(filename)))
        self.data = None
        self.yaml = abstractYaml()
        touchFile(filename)
        with open(filename) as fn:
            try:
                self.data = self.yaml.load(fn.read()) or {}
            except (IOError, OSError):
                self.data = {}
            except Exception as e:
                raise PBException("Error loading {0}: {1}".format(filename, str(e)))
        assert isinstance(self.data, dict)


    def get(self):
        " Return the data from the config file as a dict "
        return self.data or {}

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
