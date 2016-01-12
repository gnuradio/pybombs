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
import os.path as op
import shutil
import yaml
from pybombs.commands import CommandBase
from pybombs.utils import dict_merge
from pybombs.utils import subproc
from pybombs.utils import confirm
from pybombs import fetcher

### Parser Helpers
def setup_subsubparser_initsdk(parser):
    parser.add_argument(
        'sdkname',
        help="SDK Package Name",
        nargs=1,
    )

def setup_subsubparser_init(parser):
    parser.add_argument(
        'path',
        help="Path to the new prefix (defaults to CWD).",
        nargs="?",
        default=os.getcwd(),
    )
    parser.add_argument(
        '--sdk',
        dest='sdkname',
        help="Initialize prefix with SDK Package",
    )
    parser.add_argument(
        '-a', '--alias',
        help="If specified, store an alias to this new prefix in the local config file.",
    )
    parser.add_argument(
        '--virtualenv', action='store_true',
        help="Use this to make the new prefix also a virtualenv. Args for virtualenv may be passed in here",
    )

### Class definition
class Prefix(CommandBase):
    """
    Prefix operations
    """
    cmds = {
        'prefix': 'Prefix commands',
    }

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
                require_prefix=(args.prefix_command != 'init'),
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
        self._install_sdk_to_prefix(
            self.args.sdkname[0],
        )

    def _run_init(self):
        """
        pybombs prefix init
        """
        # Make sure the directory is writable
        path = op.abspath(op.normpath(self.args.path))
        if not op.isdir(path):
            self.log.info("Creating directory `{0}'".format(path))
            os.mkdir(path)
        assert op.isdir(path)
        if not os.access(path, os.W_OK|os.X_OK):
            self.log.error("Cannot write to prefix path `{0}'.".format(path))
            exit(1)

        # Make sure that a pybombs directory doesn't already exist
        test_path = op.join(path, ".pybombs")
        if op.exists(test_path):
            self.log.error("Ignoring. A prefix already exists in `{0}'".format(path))
            return

        # Copy template
        # TODO: I'm not too happy about this, all the hard coded stuff. Needs
        # cleaning up, for sure. Especially that setup_env.sh stuff at the end.
        # Ideally, we could switch prefix templates.
        self.log.info("Initializing PyBOMBS prefix in `{0}'...".format(path))
        skel_dir = op.join(self.cfg.module_dir, 'skel')
        for p in os.listdir(skel_dir):
            if op.exists(op.join(path, p)):
                self.log.obnoxious("Skipping {0}".format(p))
                continue
            self.log.obnoxious("Copying {0}".format(p))
            p_full = op.join(skel_dir, p)
            if op.isdir(p_full):
                shutil.copytree(
                    p_full, op.join(path, p),
                    ignore=shutil.ignore_patterns('.ignore')
                )
            else:
                shutil.copy(p_full, path)
        open(op.join(path, 'setup_env.sh'), 'w').write(
            open(op.join(skel_dir, 'setup_env.sh')).read().format(
                prefix_dir=path,
            )
        )
        # Register alias
        if self.args.alias is not None:
            if self.prefix is not None and \
                self.prefix.prefix_aliases.get(self.args.alias) is not None \
                and not confirm("Alias `{0}' already exists, overwrite?".format(self.args.alias)):
                    self.log.warn('Aborting.')
                    return 1
            self.cfg.update_cfg_file({'prefix_aliases': {self.args.alias: path}})
        # Create virtualenv if so desired
        if self.args.virtualenv:
            self.log.info("Creating Python virtualenv in prefix...")
            venv_args = ['virtualenv']
            venv_args.append(path)
            subproc.monitor_process(args=venv_args)
        # Install SDK if so desired
        if self.args.sdkname is not None:
            self.log.info("Reloading configuration...")
            self.cfg.load(select_prefix=path)
            self.prefix = self.cfg.get_active_prefix()
            self.inventory = self.prefix.inventory
            self._install_sdk_to_prefix(self.args.sdkname)

    def _install_sdk_to_prefix(self, sdkname):
        """
        Read recipe for sdkname, and install the SDK to the prefix.
        """
        from pybombs import recipe
        src_dir = self.prefix.src_dir
        cfg_file = self.prefix.cfg_file
        ### Get the recipe
        r = recipe.get_recipe(sdkname, target='sdk')
        try:
            self.log.obnoxious("Switching CWD to {0}".format(src_dir))
            if not op.isdir(src_dir):
                os.mkdir(src_dir)
            os.chdir(src_dir)
        except:
            self.log.error("Source dir required to install SDK.")
            return -1
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
            return -1
        # Clean up
        files_to_delete = [op.normpath(op.join(src_dir, r.var_replace_all(x))) for x in r.clean]
        if len(files_to_delete):
            self.log.info("Cleaning up files...")
        for ftd in files_to_delete:
            if op.commonprefix((src_dir, ftd)) != src_dir:
                self.log.warn("Not removing {ftd} -- outside source dir!".format(ftd=ftd))
                continue
            self.log.debug("Removing {ftd}...".format(ftd=ftd))
            if op.isdir(ftd):
                shutil.rmtree(ftd)
            elif op.isfile(ftd):
                os.remove(ftd)
            else:
                self.log.error("Not sure what this is: {ftd}".format(ftd=ftd))
                return -1
        ### Update the prefix-local config file
        self.log.debug("Updating config file with SDK recipe info.")
        try:
            old_cfg_data = yaml.safe_load(open(cfg_file).read()) or {}
        except IOError:
            self.log.debug("There doesn't seem to be a config file yet for this prefix.")
            old_cfg_data = {}
        # Filter out keys we don't care about:
        sdk_recipe_keys_for_config = ('config', 'packages', 'categories', 'env')
        sdk_cfg_data = {k: v for k, v in r.get_dict().iteritems() if k in sdk_recipe_keys_for_config}
        self.log.obnoxious("New data: {new}".format(new=sdk_cfg_data))
        cfg_data = dict_merge(old_cfg_data, sdk_cfg_data)
        self.log.debug("Writing updated prefix config to `{0}'".format(cfg_file))
        open(cfg_file, 'wb').write(yaml.dump(cfg_data, default_flow_style=False))

    #########################################################################
    # Sub-commands:
    prefix_cmd_name_list = {
        'info': {
            'help': 'Display information on the currently used prefix.',
            'parser': lambda p: None,
            'run': _print_prefix_info,
        },
        'init': {
            'help': 'Create and initialize a prefix.',
            'parser': setup_subsubparser_init,
            'run': _run_init,
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
