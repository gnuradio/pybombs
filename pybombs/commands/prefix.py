#
# Copyright 2015-2016 Free Software Foundation, Inc.
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

from __future__ import print_function
import os
import os.path as op
import shutil
from six import iteritems

from pybombs.commands import SubCommandBase
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
def setup_subsubparser_installsdk(parser):
    " Parser for pybombs prefix install-sdk "
    parser.add_argument(
        'sdkname',
        help="SDK Package Name",
        nargs=1,
    )

def setup_subsubparser_update(parser):
    parser.add_argument(
        '-R', '--recipe', default="default_prefix",
        help="Use this recipe to update the prefix",
    )


def setup_subsubparser_init(parser):
    " Parser for pybombs prefix init "
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
class Prefix(SubCommandBase):
    """
    Prefix operations
    """
    cmds = {
        'prefix': 'Prefix commands',
    }
    subcommands = {
        'info': {
            'help': 'Display information on the currently used prefix.',
            'subparser': lambda p: None,
            'run': lambda x: x.run_print_prefix_info,
        },
        'init': {
            'help': 'Create and initialize a prefix.',
            'subparser': setup_subsubparser_init,
            'run': lambda x: x.run_init,
        },
        'env': {
            'help': 'Print the environment variables used in this prefix.',
            'subparser': lambda p: None,
            'run': lambda x: x.run_print_prefix_env,
        },
        'write-env': {
            'help': 'Write "setup_env.sh" into the prefix.',
            'subparser': lambda p: None,
            'run': lambda x: x.run_write_env,
        },
        'install-sdk': {
            'help': 'Install an SDK into the prefix.',
            'subparser': setup_subsubparser_installsdk,
            'run': lambda x: x.run_installsdk,
        },
        'update': {
            'help': 'Update the prefix config from recipe.',
            'subparser': setup_subsubparser_update,
            'run': lambda x: x.run_update_prefix_config,
        },
    }

    @staticmethod
    def setup_subparser(parser, cmd=None):
        """
        Set up a subparser for a specific command
        """
        return SubCommandBase.setup_subcommandparser(
            parser,
            'Prefix Commands:',
            Prefix.subcommands
        )

    def __init__(self, cmd, args):
        SubCommandBase.__init__(
            self,
            cmd, args,
            load_recipes=True,
            require_prefix=(args.sub_command != 'init'),
        )

    #########################################################################
    # Subcommands
    #########################################################################
    def run_print_prefix_info(self):
        """
        pybombs prefix info
        """
        #self.log.info('Prefix dir: {0}'.format(self.prefix.prefix_dir))
        print("\x1b[32m[Default Prefix]: {0} \033[0m".format(self.cfg.get('default_prefix')))
        active_prefix = self.cfg.get_active_prefix()
        print("Available Prefixes :")
        for key, value in iteritems(active_prefix.prefix_aliases):
            print("{0} - {1}".format(key, value))

    def run_init(self):
        """
        pybombs prefix init
        """
        try:
            prefix_recipe = get_prefix_recipe(self.args.recipe)
        except PBException as ex:
            self.log.error(str(ex))
            return -1
        if prefix_recipe is None:
            self.log.error("Could not find recipe for `{0}'".format(self.args.recipe))
            return -1
        if not self._init_prefix(
                self.args.path,
                self.args.alias,
                prefix_recipe,
                self.args.sdkname,
                self.args.virtualenv
        ):
            return -1


    def run_print_prefix_env(self):
        """
        pybombs prefix env
        """
        print('Prefix env:')
        for k, v in iteritems(self.prefix.env):
            print("{0}={1}".format(k, v))

    def run_write_env(self):
        """
        pybombs "setup_env.sh" generator
        """
        if not self._write_env_file():
            return -1

    def run_installsdk(self):
        """
        pybombs prefix install-sdk
        """
        if not self._install_sdk_to_prefix(self.args.sdkname[0]):
            return -1

    def run_update_prefix_config(self):
        """
        pybombs prefix update
        """
        try:
            prefix_recipe = get_prefix_recipe(self.args.recipe)
        except PBException as ex:
            self.log.error(str(ex))
            return -1
        if prefix_recipe is None:
            self.log.error("Could not find recipe for `{0}'".format(self.args.recipe))
            return -1
        if not self._update_prefix(
                prefix_recipe,

        ):
            return -1
    #########################################################################
    # Helpers
    #########################################################################
    def _update_config_section(self, new_config_data, path):
        """
        used by multiple helpers to update the config file with new config data
        """
        if len(new_config_data):
            self.cfg.update_cfg_file(new_config_data, self.prefix.cfg_file)
            self.cfg.load(select_prefix=path)
            self.prefix = self.cfg.get_active_prefix()

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
        except (PBException, OSError, IOError):
            return False
        return True


    def _init_prefix(self, path, alias, prefix_recipe, sdkname, virtualenv=False):
        """
        pybombs prefix init
        """
        def check_path_is_valid(path):
            " Returns True if we can use path to init our prefix "
            try:
                if not sysutils.mkdir_writable(path, self.log):
                    raise PBException("Could not create writable directory.")
            except PBException:
                self.log.error("Cannot write to prefix path `{0}'.".format(path))
                return False
            from pybombs import config_manager
            if op.exists(op.join(path, config_manager.PrefixInfo.prefix_conf_dir)):
                self.log.warn("There already is a prefix in `{0}'.".format(path))
                if not confirm("Continue using this path?"):
                    self.log.error("Aborting. A prefix already exists in `{0}'".format(path))
                    return False
            return True
        def create_subdirs_and_files(path, dirs, files):
            " Create subdirs and files "
            sysutils.require_subdirs(path, [k for k, v in dirs.items() if v])
            for fname, content in files.items():
                sysutils.write_file_in_subdir(path, fname, prefix_recipe.var_replace_all(content))
        def register_alias(alias, path):
            " Write the prefix alias to the config file "
            if self.prefix is not None and \
                    self.prefix.prefix_aliases.get(alias) is not None \
                    and not confirm("Alias `{0}' already exists, overwrite?".format(alias)):
                self.log.warn('Aborting.')
                raise PBException("Could not create alias.")
            self.cfg.update_cfg_file({'prefix_aliases': {alias: path}})
        def create_virtualenv(path):
            " Create a Python virtualenv "
            self.log.info("Creating Python virtualenv in prefix...")
            venv_args = ['virtualenv']
            venv_args.append(path)
            subproc.monitor_process(args=venv_args)
        def install_sdk_to_new_prefix(sdk):
            " See if we need to install an SDK to the prefix and call the appropriate functions "
            if sdk is not None:
                self.log.info("Installing SDK recipe {0}.".format(sdk))
                self.log.info("Reloading configuration...")
                self.cfg.load(select_prefix=path)
                self.prefix = self.cfg.get_active_prefix()
                self.inventory = self.prefix.inventory
                return self._install_sdk_to_prefix(sdk)
            return True
        def install_dependencies(deps):
            " Install dependencies "
            if len(prefix_recipe.depends):
                self.log.info("Installing default packages for prefix...")
                self.log.info("".join(["\n  - {0}".format(x) for x in deps]))
                from pybombs import install_manager
                return install_manager.InstallManager().install(
                    deps,
                    'install', # install / update
                    fail_if_not_exists=False,
                    update_if_exists=False,
                    print_tree=True,
                )
            return True
        # Go, go, go!
        path = op.abspath(op.normpath(path))
        if not check_path_is_valid(path):
            return False
        self.cfg.load(select_prefix=path)
        self.prefix = self.cfg.get_active_prefix()
        create_subdirs_and_files(path, prefix_recipe.dirs, prefix_recipe.files)
        if alias is not None:
            register_alias(alias, path)
        if len(self.cfg.get('default_prefix')) == 0:
            self.cfg.update_cfg_file({'config': {'default_prefix': alias or path}})
        if virtualenv:
            create_virtualenv(path)
        if not install_sdk_to_new_prefix(sdkname or prefix_recipe.sdk):
            return False
        self._update_config_section(prefix_recipe.config, path)
        return install_dependencies(prefix_recipe.depends)

    def _update_prefix(self, prefix_recipe):
        """
        update the current prefix config file with a given prefix_recipe
        """
        path = self.prefix.prefix_dir
        self.cfg.load(select_prefix=path)
        self._update_config_section(prefix_recipe.config, path)
        return True

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
            return False
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
            return False
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
                return False
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
        return True
