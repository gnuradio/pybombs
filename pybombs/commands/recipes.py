#
# Copyright 2015-2016 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
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
""" PyBOMBS command: recipes """

from __future__ import print_function
import re
import os
import shutil
import sys
from pybombs.utils import confirm
from pybombs.commands import SubCommandBase
from pybombs.config_file import PBConfigFile
from pybombs.fetcher import Fetcher
from pybombs.package_manager import PackageManager
from pybombs.recipe_manager import RecipeListManager
from pybombs import recipe
from pybombs.utils import tables
from pybombs.pb_exception import PBException

#############################################################################
# Subcommand arg parsers
#############################################################################
def setup_subsubparser_add(parser):
    parser.add_argument(
        'alias',
        help="Name of new recipe location",
        nargs=1,
    )
    parser.add_argument(
        'uri',
        help="Location of recipes (URL or directory)",
        nargs=1,
    )
    parser.add_argument(
        '-f', '--force',
        help="Force additions", action='store_true',
    )
def setup_subsubparser_remove(parser):
    parser.add_argument(
        'alias',
        help="Name of recipe location to remove",
        nargs='+',
    )
def setup_subsubparser_update(parser):
    parser.add_argument(
        'alias',
        help="Name of recipe location to update",
        nargs='*',
    )
def setup_subsubparser_list(parser):
    parser.add_argument(
        '-l', '--list',
        help="List only packages that match pattern (default is to list any)",
        default=None,
    )
    parser.add_argument(
        '-i', '--installed',
        help="List only packages that are installed (default is to list all)",
        action='store_true',
    )
    parser.add_argument(
        '-x', '--in-prefix',
        help="List only packages that are installed into prefix (implies -i, default is to list all)",
        action='store_true',
    )
    parser.add_argument(
        '--format',
        help="Comma-separated list of columns",
        default="id,path,installed_by",
    )
    parser.add_argument(
        '--sort-by',
        help="Column to sort output by",
        default='id',
    )

#############################################################################
# Command class
#############################################################################
class Recipes(SubCommandBase):
    """
    pybombs recipes <foo>
    """
    cmds = {
        'recipes': 'Manage recipe lists',
    }
    subcommands = {
        'add': {
            'help': 'Add a new recipes location.',
            'subparser': setup_subsubparser_add,
            'run': lambda x: x.run_add
        },
        'remove': {
            'help': 'Remove a recipes location.',
            'subparser': setup_subsubparser_remove,
            'run': lambda x: x.run_remove,
        },
        'update': {
            'help': 'Update recipes with a remote repository.',
            'subparser': setup_subsubparser_update,
            'run': lambda x: x.run_update,
        },
        'list': {
            'help': 'List recipes.',
            'subparser': setup_subsubparser_list,
            'run': lambda x: x.run_list,
        },
        'list-repos': {
            'help': 'List recipes repositories.',
            'subparser': None,
            'run': lambda x: x.run_list_recipe_repos,
        },
    }

    @staticmethod
    def setup_subparser(parser, cmd=None):
        """
        Set up a subparser for a specific command
        """
        return SubCommandBase.setup_subcommandparser(
                parser,
                'Recipe Commands:',
                Recipes.subcommands
        )

    def __init__(self, cmd, args):
        SubCommandBase.__init__(self,
                cmd, args,
                load_recipes=False,
                require_prefix=False,
        )

    #########################################################################
    # Subcommands
    #########################################################################
    def run_add(self):
        """
        pybombs recipes add [foo]
        """
        alias = self.args.alias[0]
        uri = self.args.uri[0]
        if not self.add_recipe_dir(alias, uri):
            return -1

    def run_remove(self):
        """
        pybombs recipes remove [aliases]
        """
        if not all([self.remove_recipe_dir(x) for x in self.args.alias]):
            return -1

    def run_update(self):
        """
        pybombs recipes update [alias]
        """
        # TODO allow directories
        aliases_to_update = self.args.alias or self.cfg.get_named_recipe_sources().keys()
        if not all([self.update_recipe_repo(x) for x in aliases_to_update]):
            return -1

    def run_list(self):
        """
        Print a list of recipes.
        """
        pkgmgr = PackageManager()
        recmgr = RecipeListManager()
        self.log.debug("Loading all package names")
        all_recipes = recmgr.list_all()
        if self.args.list is not None:
            all_recipes = [x for x in all_recipes if re.search(self.args.list, x)]
        not_installed_string = '-'
        format_pkg_list = lambda x: [not_installed_string] if not x else x
        rows = []
        row_titles = {
            'id': "Package Name",
            'path': "Recipe Filename",
            'installed_by': "Installed By",
            'available_from': "Available From",
        }
        self.args.format = [x for x in self.args.format.split(",") if len(x)]
        if any(map(lambda x: x not in row_titles, self.args.format)):
            self.log.error("Invalid column formatting: {0}".format(self.args.format))
            return -1
        print("Loading package information...", end="")
        sys.stdout.flush()
        home_dir = os.path.expanduser("~")
        for pkg in all_recipes:
            rec = recipe.get_recipe(pkg, target=None, fail_easy=True)
            if rec is None:
                print()
                self.log.warn("Recipe for `{0}' is invalid.".format(pkg))
                continue
            if rec.target != 'package':
                continue
            print(".", end="")
            sys.stdout.flush()
            row = {
                'id': pkg,
                'path': recmgr.get_recipe_filename(pkg).replace(home_dir, "~"),
                'installed_by': format_pkg_list(pkgmgr.installed(pkg, return_pkgr_name=True)),
                'available_from': ",".join(format_pkg_list(pkgmgr.exists(pkg, return_pkgr_name=True))),
            }
            if self.args.in_prefix and 'source' not in row['installed_by']:
                continue
            if row['installed_by'] == [not_installed_string] and (self.args.installed or self.args.in_prefix):
                continue
            row['installed_by'] = ",".join(row['installed_by'])
            rows.append(row)
        print("")
        tables.print_table(
                row_titles,
                rows,
                self.args.format,
                sort_by=self.args.sort_by,
        )

    def run_list_recipe_repos(self):
        """
        pybombs recipes list-repos
        """
        all_locations = self.cfg.get_recipe_locations()
        named_locations = self.cfg.get_named_recipe_dirs()
        named_sources = self.cfg.get_named_recipe_sources()
        unnamed_locations = [x for x in all_locations if not x in named_locations.values()]
        table = []
        for name in named_locations.keys():
            try:
                pref_index = all_locations.index(named_locations.get(name, "FOO"))
            except ValueError:
                pref_index = -1
            table.append({
                'name': name,
                'dir': named_locations.get(name, "FOO"),
                'source': named_sources.get(name, '-'),
                'pref': pref_index,

            })
        for loc in unnamed_locations:
            try:
                pref_index = all_locations.index(loc)
            except ValueError:
                pref_index = -1
            table.append({
                'name': '-',
                'dir': loc,
                'source': '-',
                'pref': pref_index,
            })
        tables.print_table(
            {'pref': "Index", 'name': "Name", 'dir': "Directory", 'source': "Source"},
            table,
            col_order=('dir', 'name', 'source'), # Add 'pref' here to print the index
            sort_by='pref',
        )

    #########################################################################
    # Helpers
    #########################################################################
    def add_recipe_dir(self, alias, uri):
        """
        Add recipe location:
        - If a prefix was explicitly selected, install it there
        - Otherwise, use local config file
        - Check alias is not already used
        """
        self.log.debug("Preparing to add recipe location {name} -> {uri}".format(
            name=alias, uri=uri
        ))
        # Check recipe location alias is valid:
        if re.match(r'[a-z][a-z0-9_]*', alias) is None:
            self.log.error("Invalid recipe alias: {alias}".format(alias=alias))
            return False
        if alias in self.cfg.get_named_recipe_dirs():
            if self.args.force:
                self.log.info("Overwriting existing recipe alias `{0}'".format(alias))
            elif not confirm("Alias `{0}' already exists, overwrite?".format(alias)):
                self.log.warn('Aborting.')
                return False
        store_to_prefix = self.prefix is not None and self.prefix.prefix_src in ("cli", "cwd")
        cfg_file = None
        recipe_cache = None
        if store_to_prefix:
            cfg_file = self.prefix.cfg_file
            recipe_cache_top_level = os.path.join(self.prefix.prefix_cfg_dir, self.cfg.recipe_cache_dir)
        else:
            cfg_file = self.cfg.local_cfg
            recipe_cache_top_level = os.path.join(self.cfg.local_cfg_dir, self.cfg.recipe_cache_dir)
        if not os.path.isdir(recipe_cache_top_level):
            self.log.debug("Recipe cache dir does not exist, creating {0}".format(recipe_cache_top_level))
            os.mkdir(recipe_cache_top_level)
        recipe_cache = os.path.join(recipe_cache_top_level, alias)
        self.log.debug("Storing new recipe location to {cfg_file}".format(cfg_file=cfg_file))
        assert cfg_file is not None
        assert os.path.isdir(recipe_cache_top_level)
        assert recipe_cache is not None
        assert alias
        # Now make sure we don't already have a cache dir
        if os.path.isdir(recipe_cache):
            self.log.warn("Cache dir {cdir} for remote recipe location {alias} already exists! Deleting.".format(
                cdir=recipe_cache, alias=alias
            ))
            shutil.rmtree(recipe_cache)
        if not os.path.isdir(os.path.normpath(os.path.expanduser(uri))):
            # Let the fetcher download the location
            self.log.debug("Fetching into directory: {0}/{1}".format(recipe_cache_top_level, alias))
            try:
                Fetcher().fetch_url(uri, recipe_cache_top_level, alias, {}) # No args
            except PBException as ex:
                self.log.error("Could not fetch recipes: {s}".format(str(ex)))
                return False
        # Write this to config file
        self.cfg.update_cfg_file({'recipes': {alias: uri}}, cfg_file=cfg_file)
        return True

    def remove_recipe_dir(self, alias):
        """
        Remove a recipe alias and, if applicable, its cache.
        """
        if not alias in self.cfg.get_named_recipe_dirs():
            self.log.error("Unknown recipe alias: {alias}".format(alias=alias))
            return False
        # Remove from config file
        cfg_filename = self.cfg.get_named_recipe_cfg_file(alias)
        cfg_file = PBConfigFile(cfg_filename)
        cfg_data = cfg_file.get()
        cfg_data['recipes'].pop(alias, None)
        cfg_file.save(cfg_data)
        recipe_cache_dir = os.path.join(
            os.path.split(cfg_filename)[0],
            self.cfg.recipe_cache_dir,
            alias,
        )
        # If the recipe cache is not inside a PyBOMBS dir, don't delete it.
        if self.cfg.pybombs_dir not in recipe_cache_dir:
            return True
        if os.path.exists(recipe_cache_dir):
            self.log.info("Removing directory: {cdir}".format(cdir=recipe_cache_dir))
            shutil.rmtree(recipe_cache_dir)
        return True

    def update_recipe_repo(self, alias):
        """
        Update a remote recipe location by its alias name.
        """
        try:
            uri = self.cfg.get_named_recipe_sources()[alias]
            recipes_dir = self.cfg.get_named_recipe_dirs()[alias]
        except KeyError:
            self.log.error("Error looking up recipe alias '{alias}'".format(alias=alias))
            return False
        if os.path.isdir(uri):
            self.log.debug("`{0}' is a directory, can't run an update operation.".format(uri))
            return True
        if not os.path.isdir(recipes_dir):
            self.log.error("Recipe location does not exist. Run `recipes add --force' to add recipes.")
            return False
        cache_dir_top_level, cache_dir = os.path.split(os.path.normpath(recipes_dir))
        # Do actual update
        self.log.info("Updating recipe location `{alias}'...".format(alias=alias))
        if not Fetcher().update_src(uri, cache_dir_top_level, cache_dir, {}):
            self.log.error("Failed to update recipe location `{alias}'...".format(alias=alias))
            return False
        return True

