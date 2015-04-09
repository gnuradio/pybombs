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
Config Manager: Takes care of loading the right config files
and reading/setting values.
"""

import os
import ConfigParser
from pybombs import pb_logging
from pybombs.commands.cmd_base import PBException

# Don't instantiate this directly, use the config_manager object
# (see below)
class ConfigManager(object):
    """

    Order of preference, from least relevant to most:
    - Internal defaults
    - Global defaults config file (/etc/pybombs/config.dat)
    - Config file in home directory
    - Config file in current prefix
    - What was specified on the command line
    """

    cfg_file_name = "config.dat"
    pybombs_dir = ".pybombs"

    # Default values + Help text:
    defaults = {
        'gituser': ('', 'Username for GIT access'),
        'gitcache': ('', 'Directory of git cache repository'),
        'prefix': ('/usr/local/', 'Install Prefix'),
        'satisfy_order': (
            'native,src',
            'Order in which to attempt installations when available, options are: src, native'
        ),
        'forcepkgs': (
            '',
            'Comma separated list of package names to assume are already installed'
        ),
        'forcebuild ': (
            'gnuradio,uhd,gr-air-modes,gr-osmosdr,gr-iqbal,gr-fcdproplus,uhd,rtl-sdr,osmo-sdr,hackrf,gqrx,bladerf,airspy',
            'Comma separated list of package names to always build from source'
        ),
        'timeout': (
            '30',
            'Time the monitor thread waits (in seconds) before retrying downloads'
        ),
        'cmakebuildtype': (
            'RelWithDebInfo',
            'CMAKE_BUILD_TYPE args to pass to cmake projects, options are: Debug, Release, RelWithDebInfo, MinSizeRel'
        ),
        'builddocs': ('OFF', 'Build doxygen while compiling packages? options are: ON, OFF'),
        'CC': ('gcc', 'C Compiler Executable [gcc, clang, icc, etc]'),
        'CXX': ('g++', 'C++ Compiler Executable [g++, clang++, icpc, etc]'),
        'makewidth': ('4', 'Concurrent make threads [1,2,4,8...]')
    }

    def __init__(self, cfg_file=None, prefix_dir=None):
        ## Set up logger:
        self.log = pb_logging.logger
        ## Setup cfg_cascade:
        # self.cfg_cascade is a list of dicts. The higher the index,
        # the more important the dict.
        # Zeroth layer: The default values.
        self.cfg_cascade = [{k: v[0] for k, v in self.defaults.iteritems()},]
        # Global defaults TODO fix hard-coded path
        self._append_cfg_from_file(os.path.join("/etc/pybombs", self.cfg_file_name))
        # Home directory:
        self._append_cfg_from_file(os.path.join(self.get_pybombs_dir(), self.cfg_file_name))
        # Current prefix:
        self._append_cfg_from_file(os.path.join(self.get_pybombs_dir(prefix_dir), self.cfg_file_name))
        # Command line:
        if cfg_file is not None:
            self._append_cfg_from_file(os.path.join(self.get_local_pybombs_dir(), self.cfg_file_name))
        # Append an empty one. This is what we use when set() is called
        # to change settings at runtime.
        self.cfg_cascade.append({})
        # After this, no more dicts should be appended to cfg_cascade.
        print self.cfg_cascade

    def _append_cfg_from_file(self, cfg_filename):
        """
        Load file filename, interpret it as a config file
        and append to cfg_cascade
        """
        self.log.debug("Reading config info from file: {0}".format(cfg_filename))
        cfg_parser = ConfigParser.ConfigParser()
        cfg_parser.read(cfg_filename)
        if cfg_parser.has_section("config"):
            item_list = cfg_parser.items("config")
            self.cfg_cascade.append({item[0]: item[1] for item in item_list})
        else:
            self.log.debug("Config file not found or does not have [config] section.")
        if len(self.cfg_cascade[-1]) == 0:
            self.log.debug("Empty config data set.")


    def get_pybombs_dir(self, prefix_dir=None):
        """
        Return the PyBOMBS config directory.
        On Linux systems, this would be ~/.pybombs/ if no prefix_dir
        is defined, or <prefix_dir>/.pybombs if a prefix_dir is defined.
        """
        if prefix_dir is None:
            prefix_dir = os.path.expanduser("~")
        return os.path.join(prefix_dir, self.pybombs_dir)


    def get(self, key):
        """ Return the value for a given key. """
        for set_of_vals in reversed(self.cfg_cascade):
            if key in set_of_vals.keys():
                return set_of_vals[key]
        raise PBException("Invalid configuration key: {}".format(key))


    def set(self, key, value):
        """
        Set a configuration setting. This is not persistent!
        Settings written here will take precedence over any other
        settings.
        """
        self.cfg_cascade[-1][key] = value


    def get_help(self, key):
        """
        Return a short help string for a given key.
        Will return an empty string if the key is not available.
        """
        if key in self.defaults.keys():
            return self.defaults[key][1]
        return ""


# This is what you want to use
config_manager = ConfigManager()

# Some test code:
if __name__ == "__main__":
    print config_manager.get("satisfy_order")
    config_manager.set("satisfy_order", "foo,bar")
    print config_manager.get("satisfy_order")
    print config_manager.get_help("satisfy_order")

