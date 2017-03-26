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
""" PyBOMBS command: config """

from __future__ import print_function
from pybombs.commands import CommandBase

class AutoConfigurator(object):
    " Generates suitable values automatically. "
    def __init__(self, log):
        self.log = log

    def get_auto_config_settings(self, cfg_keys):
        """
        Go through a list of config keys, and automatically determine suitable
        values.
        """
        get_method_name = lambda x: "_auto_config_{0}".format(x.replace('-', '_'))
        return {k: getattr(self, get_method_name(k))()
                for k in cfg_keys
                if hasattr(self, get_method_name(k))}

    def _auto_config_makewidth(self):
        " Automatically set: makewidth "
        import multiprocessing
        return multiprocessing.cpu_count()

    def _auto_config_packagers(self):
        " Automatically set: packagers "
        from pybombs import config_manager
        from pybombs import packagers
        pkgrs = packagers.filter_available_packagers(
            config_manager.ConfigManager.defaults.get('packagers')[0],
            packagers.__dict__.values(),
            self.log
        )
        available_pkgrs = ",".join([pkgr.name for pkgr in pkgrs])
        return available_pkgrs

    def _auto_config_elevate_pre_args(self):
        " Automatically set: elevate_pre_args "
        from pybombs.utils import sysutils
        if sysutils.which('sudo'):
            return ['sudo', '-H']
        if sysutils.which('pkexec'):
            return ['pkexec']
        return ''

    def _auto_config_git_cache(self):
        " Automatically set: git-cache "
        import os.path
        from pybombs import config_manager
        from pybombs.commands.git import DEFAULT_GITCACHE_PATH
        return os.path.join(
            config_manager.config_manager.get_pybombs_dir(),
            DEFAULT_GITCACHE_PATH
        )

class AutoConfig(CommandBase):
    """ Remove a package from this prefix """
    cmds = {
        'auto-config': 'Run an automatic configuration routine',
    }

    @staticmethod
    def setup_subparser(parser, cmd=None):
        """
        Set up a subparser for 'config'
        """
        parser.add_argument(
            '-c', '--config-file',
            help="Specify the config file to update",
        )
        parser.add_argument(
            '-s', '--system', action='store_true', default=None,
            help="Store results in a system-wide configuration file (supersedes -c)",
        )

    def __init__(self, cmd, args):
        CommandBase.__init__(
            self,
            cmd, args,
            load_recipes=False,
            require_prefix=False,
        )
        # Figure out which config file to write to
        self.cfg_file = self.get_cfg_file(args)
        self.log.info("Using config file: {0}".format(self.cfg_file))

    def get_cfg_file(self, args):
        " Return the path to a config file to update "
        prefix = self.cfg.get_active_prefix()
        if args.config_file is not None:
            return args.config_file
        elif prefix.prefix_dir is not None and prefix.prefix_src == "cli":
            return prefix.cfg_file

    def run(self):
        " Go, go, go! "
        auto_config_settings = AutoConfigurator(self.log).get_auto_config_settings(self.cfg.keys())
        self.cfg.update_cfg_file(
            new_data={'config': auto_config_settings},
            cfg_file=self.cfg_file,
        )

