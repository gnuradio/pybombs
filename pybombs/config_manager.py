#!/usr/bin/env python
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

import re
import os
import argparse
import subprocess
import yaml

import pb_logging
from pb_exception import PBException
from pybombs.utils import dict_merge

def extract_cfg_items(filename, section, throw_ex=True):
    """
    Read section from a config file and return it as a dict.
    Will throw KeyError if section does not exist.
    """
    cfg_data = yaml.safe_load(open(filename).read())
    try:
        return cfg_data[section]
    except KeyError as e:
        if throw_ex:
            raise e
    return {}

class PrefixInfo(object):
    """
    Stores information about the current prefix being used.
    """
    prefix_conf_dir = '.pybombs'
    env_prefix_var = 'PYBOMBS_PREFIX'
    env_srcdir_var = 'PYBOMBS_PREFIX_SRC'
    inv_file_name = 'inventory.yml'
    setup_env_key = 'setup_env'
    default_config_info = {
            'prefix_aliases': {},
            'prefix_config_dir': {},
            'env': {},
            'recipes': {},
            'packages': {'gnuradio': 'forcebuild'},
            'categories': {'common': 'forcebuild'},
            'config': {},
    }

    def __init__(self, args, cfg_list):
        self.log = pb_logging.logger.getChild("ConfigManager.PrefixInfo")
        self.prefix_dir = None
        self.prefix_cfg_dir = None
        self.prefix_src = None
        self.alias = None
        self.src_dir = None
        self.cfg_file = None
        self.inv_file = None
        self.recipe_dir = None
        self.target_dir = None
        self.env = os.environ
        self._cfg_info = self.default_config_info
        # 1) Load the config info
        for cfg_file in reversed(cfg_list):
            self._cfg_info = self._merge_config_info_from_file(cfg_file, self._cfg_info)
        # 2) Find the prefix directory
        self._find_prefix_dir(args)
        if self.prefix_dir is None:
            self.log.warn("Cannot establish a prefix directory. This may cause issues down the line.")
            return
        assert self.prefix_dir is not None
        if self.alias is not None and self._cfg_info['prefix_config_dir'].has_key(self.alias):
            self.prefix_cfg_dir = self._cfg_info['prefix_config_dir'][self.alias]
            self.log.debug("Choosing prefix config dir from alias: {}".format(self.prefix_cfg_dir))
        elif self._cfg_info['prefix_config_dir'].has_key(self.prefix_dir):
            self.prefix_cfg_dir = self._cfg_info['prefix_config_dir'][self.prefix_dir]
            self.log.debug("Choosing prefix config dir from path lookup in prefix_config_dir: {}".format(self.prefix_cfg_dir))
        else:
            self.prefix_cfg_dir = os.path.join(self.prefix_dir, self.prefix_conf_dir)
            self.log.debug("Choosing default prefix config dir: {}".format(self.prefix_cfg_dir))
        if not os.path.isdir(self.prefix_cfg_dir):
            self.log.debug("Config dir does not yet exist, creating it.")
            os.mkdir(self.prefix_cfg_dir)
        # 3) Find the config file
        self.cfg_file = os.path.join(self.prefix_cfg_dir, ConfigManager.cfg_file_name)
        config_section = {}
        if not os.path.isfile(self.cfg_file):
            self.log.warn("Prefix configuration file not found: {}".format(self.cfg_file))
            self.cfg_file = None
        else:
            config_section = extract_cfg_items(self.cfg_file, 'config', False)
            self._cfg_info = self._merge_config_info_from_file(self.cfg_file, self._cfg_info)
        # 4) Find the src dir
        self.src_dir = config_section.get('srcdir', os.path.join(self.prefix_dir, 'src'))
        self.log.debug("Prefix source dir is: {}".format(self.src_dir))
        # 5) Find the inventory file
        self.inv_file = os.path.join(self.prefix_cfg_dir, self.inv_file_name)
        if not os.path.isfile(self.inv_file):
            self.log.warn("Prefix inventory file not found: {}".format(self.inv_file))
        # 6) Prefix-specific recipes. There's two places for these:
        # - A 'recipes/' subdirectory
        # - Anything declared in the config.yml file inside the prefix
        self.recipe_dir = config_section.get('recipes', os.path.join(self.prefix_dir, 'recipes'))
        if os.path.isdir(self.recipe_dir):
            self.log.debug("Prefix-local recipe dir is: {}".format(self.recipe_dir))
        else:
            self.recipe_dir = None
        # 7) Load environment
        # If there's a setup_env option in the current config file, we use that
        if config_section.has_key(self.setup_env_key):
            self.log.debug('Loading environment from shell script: {}'.format(config_section[self.setup_env_key]))
            self.env = self._load_environ_from_script(config_section[self.setup_env_key])
        # Set some defaults:
        self.env[self.env_prefix_var] = self.prefix_dir
        self.env[self.env_srcdir_var] = self.src_dir
        # env: sections are always respected:
        for k, v in self._cfg_info['env'].iteritems():
            self.env[k.upper()] = os.path.expandvars(v.strip())
        # 8) Keep relevant config sections as attributes
        for k, v in self._cfg_info.iteritems():
            if k == 'env' or not k in self.default_config_info.keys():
                continue
            setattr(self, k, v)

    def _merge_config_info_from_file(self, cfg_file, cfg_data={}):
        """
        Load a config file, load its contents, and merge it into cfg_info.
        Return the result.
        """
        try:
            self.log.debug('Inspecting config file: {}'.format(cfg_file))
            cfg_data_new = yaml.safe_load(open(cfg_file, 'r').read())
        except Exception as e:
            self.log.debug('Well, looks like that failed.')
            return cfg_data
        return dict_merge(cfg_data, cfg_data_new)

    def _find_prefix_dir(self, args):
        """
        Find the current prefix' directory.
        Order is:
        1) From the command line (-p switch; either an alias, or a directory)
        2) Environment variable (see env_prefix_var)
        3) CWD (if it has a .pybombs subdir and is not the home directory)
        4) The config option called 'default_prefix'

        If all of these fail, we have no prefix.
        """
        if args.prefix is not None:
            if self._cfg_info['prefix_aliases'].has_key(args.prefix):
                self.log.debug("Resolving prefix alias {}.".format(args.prefix))
                self.alias = args.prefix
                args.prefix = self._cfg_info['prefix_aliases'][args.prefix]
            if not os.path.isdir(args.prefix):
                raise PBException("Can't open prefix: {}".format(args.prefix))
            self.prefix_dir = args.prefix
            self.prefix_src = 'cli'
            self.log.debug("Choosing prefix dir from command line: {}".format(self.prefix_dir))
            return
        if os.environ.has_key(self.env_prefix_var) and os.path.isdir(os.environ[self.env_prefix_var]):
            self.prefix_dir = os.environ[self.env_prefix_var]
            self.prefix_src = 'env'
            self.log.debug('Using environment variable {} as prefix ({})'.format(self.env_prefix_var, self.prefix_dir))
        if os.getcwd() != os.path.expanduser('~') and os.path.isdir(os.path.join('.', self.prefix_conf_dir)):
            self.prefix_dir = os.getcwd()
            self.prefix_src = 'cwd'
            self.log.debug('Using CWD as prefix ({})'.format(self.prefix_dir))
            return
        if self._cfg_info.get('config', {}).get('default_prefix'):
            self.prefix_dir = self._cfg_info['config']['default_prefix']
            if self._cfg_info['prefix_aliases'].has_key(self.prefix_dir):
                self.log.debug("Resolving prefix alias {}.".format(self.prefix_dir))
                self.prefix_dir = self._cfg_info['prefix_aliases'][self.prefix_dir]
            self.log.debug('Using default_prefix as prefix ({})'.format(self.prefix_dir))
            self.prefix_src = 'default'
            return
        self.prefix_src = None
        self.prefix_dir = None

    def _load_environ_from_script(self, setup_env_file):
        """
        Run setup_env_file, return the new env
        FIXME make this portable!
        """
        self.log.debug('Loading environment from shell script: {}'.format(setup_env_file))
        # It would be nice if we could do os.path.expandvars() with a custom
        # env, wouldn't it
        setup_env_file = setup_env_file.replace('$PYBOMBS_PREFIX', self.prefix_dir)
        setup_env_file = setup_env_file.replace('${PYBOMBS_PREFIX}', self.prefix_dir)
        # TODO add some checks this is a legit script
        # Damn, I hate just running stuff :/
        # TODO unportable command:
        separator = '<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>'
        get_env_cmd = "source {env_file} && echo '{sep}' && env".format(env_file=setup_env_file, sep=separator)
        try:
            script_output = subprocess.check_output(get_env_cmd, shell=True)
        except subprocess.CalledProcessError as e:
            self.log.error("Trouble sourcing file {env_file}".format(setup_env_file))
            exit(1)
        env_output = script_output.split(separator)[-1]
        # TODO assumption is that env_output now just holds the env output
        env_output = env_output.split('\n')
        env = {}
        for env_line in env_output:
            env_line = env_line.strip()
            if len(env_line) == 0:
                continue
            k, v = env_line.split('=', 1)
            env[k] = v
        return env


# Don't instantiate this directly, use the config_manager object
# (see below)
class ConfigManager(object):
    """
    Order of preference, from least relevant to most:
    - Internal defaults
    - Global defaults config file (/etc/pybombs/config.yml)
    - Config file in home directory
    - Config file in current prefix
    - What was specified on the command line
    """
    global_base_dir = "/etc/pybombs" # TODO we may want to change this
    cfg_file_name = "config.yml"
    pybombs_dir = ".pybombs"
    recipe_cache_dir = 'recipes'

    # Default values + Help text:
    defaults = {
        'gituser': ('', 'Username for GIT access'),
        'gitcache': ('', 'Directory of git cache repository'),
        'prefix': ('/usr/local/', 'Install Prefix'),
        'satisfy_order': (
            'native, src',
            'Order in which to attempt installations when available, options are: src, native'
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
        'cc': ('', 'C Compiler Executable [gcc, clang, icc, etc]'),
        'cxx': ('', 'C++ Compiler Executable [g++, clang++, icpc, etc]'),
        'makewidth': ('4', 'Concurrent make threads [1,2,4,8...]'),
        'packagers': ('apt-get', 'Priority of non-source package managers'),
    }
    LAYER_DEFAULT = 0
    LAYER_GLOBALS = 1
    LAYER_HOME = 2
    LAYER_PREFIX = 3
    LAYER_CMDLINE_FILE = 4
    LAYER_CMDLINE_ARGS = 5
    LAYER_VOLATILE = 6

    def __init__(self,):
        ## Get command line args:
        parser = argparse.ArgumentParser(add_help=False)
        self.setup_parser(parser)
        args = parser.parse_known_args()[0]
        cfg_files = []
        ## Set verbosity level:
        verb_offset = args.verbose - args.quiet
        verb_level = pb_logging.logger.getEffectiveLevel() - 10 * verb_offset
        if verb_level < pb_logging.OBNOXIOUS:
            verb_level = pb_logging.OBNOXIOUS
        pb_logging.logger.setLevel(verb_level)
        ## Set up logger:
        self.log = pb_logging.logger.getChild("ConfigManager")
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
        self.local_cfg_dir = self.get_pybombs_dir()
        self.local_cfg = os.path.join(self.local_cfg_dir, self.cfg_file_name)
        if self._append_cfg_from_file(self.local_cfg):
            cfg_files.insert(0, self.local_cfg)
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
        # Find recipe templates:
        self._template_dir = os.path.join(os.path.dirname(pb_logging.__file__), 'templates')
        self.log.debug("Template directory: {}".format(self._template_dir))
        ## Init prefix:
        self._prefix_info = PrefixInfo(args, cfg_files)
        self.cfg_cascade[self.LAYER_PREFIX] = self._prefix_info.config
        self.log.debug("Add prefix config options: {cfg}".format(cfg=self.cfg_cascade[self.LAYER_PREFIX]))
        ## Init recipe-lists:
        # Go through cfg files, then env variable, then command line args
        # From command line:
        self._recipe_locations = []
        self._named_recipe_locations = {}
        self._named_recipe_sources = {}
        for r_loc in args.recipes:
            if r_loc:
                self._recipe_locations.append(r_loc)
        # From environment variable:
        if len(os.environ.get("PYBOMBS_RECIPE_DIR", "").strip()):
            self._recipe_locations += os.environ.get("PYBOMBS_RECIPE_DIR", "").split(";")
        # From prefix info:
        if self._prefix_info.recipe_dir is not None:
            self._recipe_locations.append(self._prefix_info.recipe_dir)
        # From config files (from here, recipe locations are named):
        for cfg_file in reversed(cfg_files):
            recipe_locations = extract_cfg_items(cfg_file, "recipes", False)
            for name, uri in recipe_locations.iteritems():
                local_recipe_dir = self.resolve_recipe_uri(
                    uri, name, os.path.join(os.path.split(cfg_file)[0], 'recipes')
                )
                self._recipe_locations.append(local_recipe_dir)
                self._named_recipe_locations[name] = uri
                self._named_recipe_sources[name] = cfg_file
        self.log.debug("Full list of recipe locations: {}".format(self._recipe_locations))
        self.log.debug("Named recipe locations: {}".format(self._named_recipe_locations))


    def _append_cfg_from_file(self, cfg_filename):
        """
        Load file filename, interpret it as a config file
        and append to cfg_cascade

        Returns True if loading the config file was successful.
        """
        self.log.debug("Reading config info from file: {0}".format(cfg_filename))
        try:
            cfg_data = yaml.safe_load(open(cfg_filename).read())
        except Exception as e:
            self.log.debug("Parsing config file failed ({cfgf}).".format(cfgf=cfg_filename))
            self.cfg_cascade.append({})
            return False
        config_items = cfg_data.get('config', {})
        self.log.debug('New config items: {items}'.format(items=config_items))
        self.cfg_cascade.append(config_items)
        return True

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
        if default is not None:
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

    def get_named_recipe_locations(self):
        """
        Returns a dictionary of named recipe locations. Note that
        these are not resolved locations.
        """
        return self._named_recipe_locations

    def get_named_recipe_source(self, recipe_alias):
        """
        Returns the path of the config file which declared a recipe by name.
        """
        return self._named_recipe_sources[recipe_alias]

    def get_template_dir(self):
        """
        Returns the location of the .lwt files
        """
        return self._template_dir

    def resolve_recipe_uri(self, uri, name, cache_dir):
        """
        Turn a recipe URI into a directory.

        There's two ways this goes: Either, the recipe URI
        is already a directory, then return that. Or it's a remote
        URI; in that case, return the cache directory.
        """
        if re.match(r'^[a-z]{3,4}\+', uri) is None:
            return uri
        return os.path.join(cache_dir, name)

    def get_package_flags(self, pkgname, categoryname=None):
        """
        Return all the package flags of pkgname as a dictionary.
        If pkgname doesn't have any package flags, return an empty dict.

        If categoryname is provided, it will load the category flags first
        and then merge the package flags on top of it.
        """
        return dict_merge(
            getattr(self._prefix_info, 'categories').get(categoryname, {}),
            getattr(self._prefix_info, 'packages').get(pkgname, {})
        )

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
            help="Set a config.yml option via command line. May be used multiple times",
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
        parser.add_argument(
            '-q', '--quiet',
            help="Reduce the output",
            action='count',
            default=0,
        )
        parser.add_argument(
            '-v', '--verbose',
            help="More output",
            action='count',
            default=0,
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
