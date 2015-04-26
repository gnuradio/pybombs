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
Used as a central cache for all kinds of settings.
"""

import os
import argparse
import ConfigParser
import pb_logging
from pb_exception import PBException

def extract_cfg_items(filename, section, throw_ex=True):
    """
    Read section from a config file and return it as a dict.
    Will throw KeyError if section does not exist.
    """
    cfg_parser = ConfigParser.ConfigParser()
    cfg_parser.read(filename)
    if cfg_parser.has_section(section):
        item_list = cfg_parser.items(section)
        item_list = {item[0]: item[1] for item in item_list}
    else:
        if not throw_ex:
            return {}
        raise KeyError
    return item_list

class PrefixInfo(object):
    """
    Stores information about the current prefix being used.
    """
    prefix_conf_dir = '.pybombs'
    inv_file_name = 'inventory.dat'

    def __init__(self, args, cfg_list):
        self.log = pb_logging.logger.getChild("ConfigManager.PrefixInfo")
        self.prefix_dir = None
        self.src_dir = None
        self.cfg_file = None
        self.inv_file = None
        self.recipe_dir = None
        item_list = None
        # 1) Find the directory
        if args.prefix is not None: # Either on the command line ...
            if not os.path.isdir(args.prefix):
                raise PBException("Can't open prefix directory: {}".format(args.prefix))
            self.prefix_dir = args.prefix
            self.log.debug("Choosing prefix dir from command line: {}".format(self.prefix_dir))
            if args.prefix_conf is not None:
                self.cfg_file = args.prefix_conf
        else: # ... or in one of the config files:
            for cfg_file in cfg_list:
                cfg_parser = ConfigParser.ConfigParser()
                cfg_parser.read(cfg_file)
                try:
                    item_list = extract_cfg_items(cfg_file, "prefix")
                    if not item_list.has_key("dir") or not os.path.isdir(item_list["dir"]):
                        raise PBException(
                            "Invalid [prefix] section in file {} (invalid dir specified)"
                            .format(cfg_file)
                        )
                    self.prefix_dir = item_list["dir"]
                    self.cfg_file = cfg_file
                    break
                except KeyError:
                    continue
        if self.prefix_dir is None:
            self.log.warn("Cannot establish a prefix directory. This may cause issues down the line.")
            return
        self.log.debug("Prefix dir is: {}".format(self.prefix_dir))
        assert self.prefix_dir is not None
        # 2) Find the config file
        cfg_subdir = os.path.join(self.prefix_dir, self.prefix_conf_dir)
        if self.cfg_file is None:
            if not os.path.isdir(cfg_subdir):
                self.log.info("Generating prefix config dir {}.".format(cfg_subdir))
                os.mkdir(cfg_subdir)
            self.cfg_file = os.path.join(self.prefix_dir, self.prefix_conf_dir, ConfigManager.cfg_file_name)
        if not os.path.isfile(self.cfg_file):
            self.log.info("Generating skeleton prefix configuration.")
            open(self.cfg_file, 'w').write("[config]\n\n[prefix]\n")
        self.log.debug("Prefix config file is: {}".format(self.cfg_file))
        if item_list is None:
            try:
                item_list = extract_cfg_items(self.cfg_file, "prefix")
            except KeyError:
                item_list = {}
        assert self.cfg_file is not None
        # 3) Find the src dir
        if item_list.has_key("srcdir"):
            self.src_dir = item_list["srcdir"]
        else:
            self.src_dir = os.path.join(self.prefix_dir, 'src')
        self.log.debug("Prefix source dir is: {}".format(self.src_dir))
        if not os.path.isdir(self.src_dir):
            self.log.info("Creating src directory: {}".format(self.src_dir))
            os.mkdir(self.src_dir)
        assert self.src_dir is not None
        # 4) Find the inventory file
        if item_list.has_key("inventory"):
            self.inv_file = item_list["inventory"]
        else:
            self.inv_file = os.path.join(self.prefix_dir, self.prefix_conf_dir, self.inv_file_name)
        self.log.debug("Prefix inventory file is: {}".format(self.inv_file))
        if not os.path.isfile(self.inv_file):
            self.log.info("Creating empty inventory file: {}".format(self.inv_file))
            open(self.inv_file, 'w').write("[config]\n\n[prefix]\n")
        assert self.inv_file is not None
        # 5) Local recipe directory
        if item_list.has_key("recipes"):
            self.recipe_dir = item_list["recipes"]
        elif os.path.isdir(os.path.join(cfg_subdir, 'recipes')):
            self.recipe_dir = os.path.join(cfg_subdir, 'recipes')
        self.log.debug("Prefix-local recipe dir is: {}".format(self.recipe_dir))


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
    global_base_dir = "/etc/pybombs" # TODO we may want to change this
    cfg_file_name = "config.dat"
    pybombs_dir = ".pybombs"

    # Default values + Help text:
    defaults = {
        'gituser': ('', 'Username for GIT access'),
        'gitcache': ('', 'Directory of git cache repository'),
        'prefix': ('/usr/local/', 'Install Prefix'),
        'satisfy_order': (
            'native, src',
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
    LAYER_DEFAULT = 0
    LAYER_GLOBALS = 1
    LAYER_HOME = 2
    LAYER_PREFIX = 3
    LAYER_CMDLINE_FILE = 4
    LAYER_CMDLINE_ARGS = 5
    LAYER_VOLATILE = 6

    def __init__(self,):
        ## Set up logger:
        self.log = pb_logging.logger.getChild("ConfigManager")
        ## Get command line args:
        parser = argparse.ArgumentParser(add_help=False)
        self.setup_parser(parser)
        args = parser.parse_known_args()[0]
        cfg_files = []
        ## Setup cfg_cascade:
        # self.cfg_cascade is a list of dicts. The higher the index,
        # the more important the dict.
        # Zeroth layer: The default values.
        self.cfg_cascade = [{k: v[0] for k, v in self.defaults.iteritems()},]
        # Global defaults
        global_cfg = os.path.join(self.global_base_dir, self.cfg_file_name)
        if self._append_cfg_from_file(global_cfg):
            cfg_files.insert(0, global_cfg)
        # Home directory:
        local_cfg = os.path.join(self.get_pybombs_dir(), self.cfg_file_name)
        if self._append_cfg_from_file(local_cfg):
            cfg_files.insert(0, local_cfg)
        # Current prefix (don't know that yet -- so skip for now)
        self.cfg_cascade.append({})
        # Config file specified on command line:
        if args.config_file is not None:
            self._append_cfg_from_file(args.config_file)
            cfg_files.insert(0, args.config_file)
        else:
            self.cfg_cascade.append({})
        # Config args specified on command line:
        cmd_line_opts = {}
        for opt in args.config:
            k, v = opt.split('=', 1)
            cmd_line_opts[k] = v
        self.cfg_cascade.append(cmd_line_opts)
        # Append an empty one. This is what we use when set() is called
        # to change settings at runtime.
        self.cfg_cascade.append({})
        # After this, no more dicts should be appended to cfg_cascade.
        assert len(self.cfg_cascade) == self.LAYER_VOLATILE + 1
        ## Init prefix:
        self._prefix_info = PrefixInfo(args, cfg_files)
        ## Init recipe-lists:
        # Go through cfg files, then env variable, then command line args
        # From command line:
        self._recipe_locations = []
        for r_loc in args.recipes:
            if r_loc:
                self._recipe_locations.append(r_loc)
        # From environment variable:
        if len(os.environ.get("PYBOMBS_RECIPE_DIR", "").strip()):
            self._recipe_locations += os.environ.get("PYBOMBS_RECIPE_DIR", "").split(";")
        # From prefix info:
        if self._prefix_info.recipe_dir is not None:
            self._recipe_locations.append(self._prefix_info.recipe_dir)
        # From config files:
        for cfg_file in cfg_files:
            recipe_locations = extract_cfg_items(cfg_file, "recipes", False)
            for loc in recipe_locations.itervalues():
                self._recipe_locations.append(loc)
        self.log.debug("Full list of recipe locations: {}".format(self._recipe_locations))


    def _append_cfg_from_file(self, cfg_filename):
        """
        Load file filename, interpret it as a config file
        and append to cfg_cascade
        """
        self.log.debug("Reading config info from file: {0}".format(cfg_filename))
        cfg_parser = ConfigParser.ConfigParser()
        cfg_parser.read(cfg_filename)
        found_cfg = False
        if cfg_parser.has_section("config"):
            item_list = cfg_parser.items("config")
            self.cfg_cascade.append({item[0]: item[1] for item in item_list})
            found_cfg = True
        else:
            self.cfg_cascade.append({})
            self.log.debug("Config file not found or does not have [config] section.")
        if len(self.cfg_cascade[-1]) == 0:
            self.log.debug("Empty config data set.")
        return found_cfg


    def get_pybombs_dir(self, prefix_dir=None):
        """
        Return the PyBOMBS config directory.
        On Linux systems, this would be ~/.pybombs/ if no prefix_dir
        is defined, or <prefix_dir>/.pybombs if a prefix_dir is defined.
        """
        if prefix_dir is None:
            prefix_dir = os.path.expanduser("~")
        return os.path.join(prefix_dir, self.pybombs_dir)


    def get(self, key, default=None):
        """ Return the value for a given key. """
        for set_of_vals in reversed(self.cfg_cascade):
            if key in set_of_vals.keys():
                return set_of_vals[key]
            elif default is not None:
                return default
        raise PBException("Invalid configuration key: {}".format(key))


    def set(self, key, value):
        """
        Set a configuration setting. This is not persistent!
        Settings written here will take precedence over any other
        settings.
        """
        self.cfg_cascade[self.LAYER_VOLATILE][key] = value


    def get_help(self, key):
        """
        Return a short help string for a given key.
        Will return an empty string if the key is not available.
        """
        if key in self.defaults.keys():
            return self.defaults[key][1]
        return ""

    def get_active_prefix(self):
        """
        Return a PrefixInfo object for the current active prefix.
        """
        return self._prefix_info

    def get_recipe_locations(self):
        """
        Returns a list of recipe locations, in order of preference
        """
        return self._recipe_locations

    def setup_parser(self, parser):
        """
        Initialize an ArgParser with all the args required for this
        class to operate.
        """
        parser.add_argument(
                '-p', '--prefix',
                help="Specify a prefix directory",
        )
        parser.add_argument(
                '--prefix-conf',
                help="Specify a prefix configuration file",
                type=file,
                default=None
        )
        parser.add_argument(
                '--config',
                help="Set a config.dat option via command line. May be used multiple times",
                action='append',
                default=[],
        )
        parser.add_argument(
                '--config-file',
                help="Specify a config file via command line",
                type=file,
                default=None,
        )
        parser.add_argument(
                '-r', '--recipes',
                help="Specify a recipe location. May be used multiple times",
                action='append',
                default=[],
        )
        return parser


# This is what you want to use
config_manager = ConfigManager()

# Some test code:
if __name__ == "__main__":
    print config_manager.get_help("satisfy_order")
    print config_manager.get("satisfy_order")
    config_manager.set("satisfy_order", "foo, bar")
    print config_manager.get("satisfy_order")

