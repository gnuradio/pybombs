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
""" PyBOMBS command: prefix """

import os
import shutil
import yaml
from pybombs.commands import CommandBase
from pybombs.utils import dict_merge
from pybombs.utils import subproc
from pybombs import recipe
from pybombs import fetcher

### Parser Helpers
def setup_subsubparser_initsdk(parser):
    parser.add_argument(
        'sdkname',
        help="SDK Package Name",
        nargs=1,
    )

### Class definition
class Prefix(CommandBase):
    """
    Prefix operations
    """
    cmds = {
        'prefix': 'Prefix commands', # TODO nicer
    }
    # These sections are copied from the recipe to the config file
    sdk_recipe_keys_for_config = ('config', 'packages', 'categories', 'env')

    @staticmethod
    def setup_subparser(parser, cmd=None):
        """
        Set up a subparser for a specific command
        """
        ###### Start of setup_subparser()
        subparsers = parser.add_subparsers(
                help="Prefix Commands:",
                dest='prefix_command',
        )
        for cmd_name, cmd_info in Prefix.prefix_cmd_name_list.iteritems():
            subparser = subparsers.add_parser(
                    cmd_name,
                    help=cmd_info['help']
            )
            cmd_info['parser'](subparser)
        return parser

    def __init__(self, cmd, args):
        CommandBase.__init__(self,
                cmd, args,
                load_recipes=True,
                require_prefix=True,
                require_inventory=True
        )

    def run(self):
        """ Go, go, go! """
        self.prefix_cmd_name_list[self.args.prefix_command]['run'](self)

    def _print_prefix_info(self):
        """
        pybombs prefix info
        """
        self.log.info('Prefix dir: {}'.format(self.prefix.prefix_dir))

    def _print_prefix_env(self):
        """
        pybombs prefix env
        """
        print('Prefix env:')
        for k, v in self.prefix.env.iteritems():
            print("{}={}".format(k, v))


    def _run_installsdk(self):
        """
        pybombs prefix install-sdk
        """
        self._install_sdk_to_prefix(self.args.sdkname[0])

    def _run_init(self):
        """
        pybombs prefix init
        """
        # tbw
        pass


    def _install_sdk_to_prefix(self, sdkname):
        """
        Read recipe for sdkname, and install the SDK to the prefix.
        """
        ### Get the recipe
        r = recipe.get_recipe(sdkname, target='sdk')
        try:
            os.chdir(self.prefix.src_dir)
        except:
            self.log.error("Source dir required to install SDK.")
            exit(1)
        ### Install the actual SDK file
        self.log.debug("Fetching SDK `{sdk}'".format(sdk=sdkname))
        fetcher.Fetcher().fetch(r)
        self.log.info("Installing SDK `{sdk}'".format(sdk=sdkname))
        # Install command
        cmd = r.var_replace_all(r.get_command('install'))
        if subproc.monitor_process(cmd, shell=True, env=os.environ) == 0:
            self.log.debug("Installation successful")
        else:
            self.log.error("Error installing SDK. Aborting.")
            exit(1)
        # Clean up
        files_to_delete = [r.var_replace_all(x) for x in r.clean]
        if len(files_to_delete):
            self.log.info("Cleaning up files...")
        for ftd in files_to_delete:
            ftd = os.path.normpath(os.path.join(self.prefix.src_dir, ftd))
            if os.path.commonprefix((self.prefix.src_dir, ftd)) != self.prefix.src_dir:
                self.log.warn("Not removing {ftd} -- outside source dir!".format(ftd=ftd))
                continue
            self.log.debug("Removing {ftd}...".format(ftd=ftd))
            if os.path.isdir(ftd):
                shutil.rmtree(ftd)
            elif os.path.isfile(ftd):
                os.remove(ftd)
            else:
                self.log.error("Not sure what this is: {ftd}".format(ftd=ftd))
                exit(1)
        ### Update the prefix-local config file
        self.log.debug("Updating config file with SDK recipe info.")
        try:
            old_cfg_data = yaml.safe_load(open(self.prefix.cfg_file).read()) or {}
        except IOError:
            self.log.debug("There doesn't seem to be a config file yet for this prefix.")
            old_cfg_data = {}
        # Filter out keys we don't care about:
        sdk_cfg_data = {k: v for k, v in r.get_dict().iteritems() if k in self.sdk_recipe_keys_for_config}
        self.log.obnoxious("New data: {new}".format(new=sdk_cfg_data))
        cfg_data = dict_merge(old_cfg_data, sdk_cfg_data)
        open(self.prefix.cfg_file, 'wb').write(yaml.dump(cfg_data, default_flow_style=False))

    #########################################################################
    # Sub-commands:
    prefix_cmd_name_list = {
            'info': {
                'help': 'Display information on the currently used prefix.',
                'parser': lambda p: None,
                'run': _print_prefix_info,
            },
            'env': {
                'help': 'Print the environment variables used in this prefix.',
                'parser': lambda p: None,
                'run': _print_prefix_info,
            },
            'install-sdk': {
                'help': 'Install an SDK into the prefix.',
                'parser': setup_subsubparser_initsdk,
                'run': _run_installsdk,
            },
    }
    #########################################################################

