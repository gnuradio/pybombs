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
from six import iteritems

from pybombs.commands import CommandBase
from pybombs.config_file import PBConfigFile
from pybombs.utils import dict_merge
from pybombs.utils import subproc
from pybombs.utils import confirm
from pybombs.utils import sysutils
from pybombs.pb_exception import PBException
from pybombs import fetcher

#############################################################################
# Sub-command sub-parsers
#############################################################################
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
    parser.add_argument(
        '-R', '--recipe', default="default_prefix",
        help="Use this recipe to set up the prefix",
    )


def setup_subsubparser_write_env(parser):
    pass

#############################################################################
# Helpers
#############################################################################
def get_prefix_recipe(recipe_name):
    " Return the prefix recipe or None "
    from pybombs import recipe
    return recipe.get_recipe(recipe_name, target='prefix', fail_easy=True)

#############################################################################
# Class definition
#############################################################################
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
        for cmd_name, cmd_info in iteritems(Prefix.prefix_cmd_name_list):
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
        return self.prefix_cmd_name_list[self.args.prefix_command]['run'](self)

    def _print_prefix_info(self):
        """
        pybombs prefix info
        """
        #self.log.info('Prefix dir: {}'.format(self.prefix.prefix_dir))
        print("\x1b[32m[Default Prefix]: {} \033[0m".format(self.cfg.get('default_prefix')))
        self.active_prefix = self.cfg.get_active_prefix()
        print("Available Prefixes :")
        for key,value in iteritems(self.active_prefix.prefix_aliases):
            print("{} - {}".format(key, value))


    def _print_prefix_env(self):
        """
        pybombs prefix env
        """
        print('Prefix env:')
        for k, v in iteritems(self.prefix.env):
            print("{}={}".format(k, v))


    def _run_installsdk(self):
        """
        pybombs prefix install-sdk
        """
        self._install_sdk_to_prefix(
            self.args.sdkname[0],
        )

    def _run_write_env(self):
        """
        pybombs "setup_env.sh" generator
        """
        if not self._write_env_file():
            return -1

    def _run_init(self):
        """
        pybombs prefix init
        """
        def register_alias(alias):
            if alias is not None:
                if self.prefix is not None and \
                        self.prefix.prefix_aliases.get(alias) is not None \
                        and not confirm("Alias `{0}' already exists, overwrite?".format(alias)):
                    self.log.warn('Aborting.')
                    raise PBException("Could not create alias.")
                self.cfg.update_cfg_file({'prefix_aliases': {self.args.alias: path}})
        # Go, go, go!
        try:
            prefix_recipe = get_prefix_recipe(self.args.recipe)
        except PBException as ex:
            self.log.error(str(ex))
            return -1
        if prefix_recipe is None:
            self.log.error("Could not find recipe for `{0}'".format(self.args.recipe))
            return -1
        # Make sure the directory is writable
        path = op.abspath(op.normpath(self.args.path))
        if not sysutils.mkdir_writable(path, self.log):
            self.log.error("Cannot write to prefix path `{0}'.".format(path))
            return -1
        # Make sure that a pybombs directory doesn't already exist
        from pybombs import config_manager
        if op.exists(op.join(path, config_manager.PrefixInfo.prefix_conf_dir)):
            self.log.error("Ignoring. A prefix already exists in `{0}'".format(path))
            return -1
        # Add subdirs
        sysutils.require_subdirs(path, [k for k, v in prefix_recipe.dirs.items() if v])
        self.cfg.load(select_prefix=path)
        self.prefix = self.cfg.get_active_prefix()
        # Create files
        for fname, content in prefix_recipe.files.items():
            sysutils.write_file_in_subdir(path, fname, prefix_recipe.var_replace_all(content))
        # Register alias
        if self.args.alias is not None:
            register_alias(self.args.alias)
        # If there is no default prefix, make this the default
        if len(self.cfg.get('default_prefix')) == 0:
            if self.args.alias is not None:
                new_default_prefix = self.args.alias
            else:
                new_default_prefix = path
            self.cfg.update_cfg_file({'config': {'default_prefix': new_default_prefix}})
        # Create virtualenv if so desired
        if self.args.virtualenv:
            self.log.info("Creating Python virtualenv in prefix...")
            venv_args = ['virtualenv']
            venv_args.append(path)
            subproc.monitor_process(args=venv_args)
        # Install SDK if so desired
        sdk = self.args.sdkname or prefix_recipe.sdk
        if sdk is not None:
            self.log.info("Installing SDK recipe {0}.".format(sdk))
            self.log.info("Reloading configuration...")
            self.cfg.load(select_prefix=path)
            self.prefix = self.cfg.get_active_prefix()
            self.inventory = self.prefix.inventory
            self._install_sdk_to_prefix(sdk)
        # Update config section
        if len(prefix_recipe.config):
            self.cfg.update_cfg_file(prefix_recipe.config, self.prefix.cfg_file)
            self.cfg.load(select_prefix=path)
            self.prefix = self.cfg.get_active_prefix()
        # Install dependencies
        if len(prefix_recipe.depends):
            self.log.info("Installing default packages for prefix...")
            self.log.info("".join(["\n  - {0}".format(x) for x in prefix_recipe.depends]))
            from pybombs import install_manager
            install_manager.InstallManager().install(
                    prefix_recipe.depends,
                    'install', # install / update
                    fail_if_not_exists=False,
                    update_if_exists=False,
                    print_tree=True,
            )

    def _write_env_file(self):
        """
        Create a setup_env.sh file in the prefix
        """
        prefix_recipe = get_prefix_recipe("default_prefix")
        if prefix_recipe is None:
            self.log.error("Could not find recipe for `{0}'".format(self.args.recipe))
            return False
        path = self.prefix.prefix_dir
        if not sysutils.dir_is_writable(path):
            self.log.error("Cannot write to prefix path `{0}'.".format(path))
            return -1
        try:
            for fname, content in prefix_recipe.files.items():
                sysutils.write_file_in_subdir(path, fname, prefix_recipe.var_replace_all(content))
        except (PBException, OSError, IOError) as ex:
            return False
        return True

    def _copy_prefix_template(self, path):
        """
        Create all the files and directories
        """
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
            old_cfg_data = PBConfigFile(cfg_file).get()
        except IOError:
            self.log.debug("There doesn't seem to be a config file yet for this prefix.")
            old_cfg_data = {}
        # Filter out keys we don't care about:
        sdk_recipe_keys_for_config = ('config', 'packages', 'categories', 'env')
        sdk_cfg_data = {k: v for k, v in iteritems(r.get_dict()) if k in sdk_recipe_keys_for_config}
        self.log.obnoxious("New data: {new}".format(new=sdk_cfg_data))
        cfg_data = dict_merge(old_cfg_data, sdk_cfg_data)
        self.log.debug("Writing updated prefix config to `{0}'".format(cfg_file))
        PBConfigFile(cfg_file).save(cfg_data)

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
            'run': _print_prefix_env,
        },
        'write-env': {
            'help': 'Write "setup_env.sh" into the prefix.',
            'parser': setup_subsubparser_write_env,
            'run': _run_write_env,
        },
        'install-sdk': {
            'help': 'Install an SDK into the prefix.',
            'parser': setup_subsubparser_initsdk,
            'run': _run_installsdk,
        },
    }
    #########################################################################
