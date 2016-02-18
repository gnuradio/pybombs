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
""" PyBOMBS command: recipes """

from __future__ import print_function
import re
import os
import shutil
import yaml
import sys
from pybombs.utils import confirm
from pybombs.commands import CommandBase
from pybombs.fetcher import Fetcher
from pybombs.package_manager import PackageManager
from pybombs.recipe_manager import RecipeListManager
from pybombs import recipe

class Recipes(CommandBase):
    """
    Manage recipe lists
    """
    cmds = {
        'recipes': 'Manage recipe lists',
    }

    @staticmethod
    def setup_subparser(parser, cmd=None):
        """
        Set up a subparser for a specific command
        """
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
                nargs=1,
            )
        def setup_subsubparser_update(parser):
            parser.add_argument(
                'alias',
                help="Name of recipe location to update",
                nargs=1,
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
        ###### Start of setup_subparser()
        subparsers = parser.add_subparsers(
                help="Recipe Commands:",
                dest='recipe_command',
        )
        recipes_cmd_name_list = {
            'add':    ('Add a new recipes location.', setup_subsubparser_add),
            'remove': ('Remove a recipes location.', setup_subsubparser_remove),
            'update': ('Update recipes with a remote repository', setup_subsubparser_update),
            'list':   ('List recipes', setup_subsubparser_list),
        }
        for cmd_name, cmd_info in recipes_cmd_name_list.iteritems():
            subparser = subparsers.add_parser(cmd_name, help=cmd_info[0])
            cmd_info[1](subparser)
        return parser


    def __init__(self, cmd, args):
        CommandBase.__init__(self,
                cmd, args,
                load_recipes=False,
                require_prefix=False,
        )

    def run(self):
        """ Go, go, go! """
        if hasattr(self.args, 'alias'):
            self.args.alias = self.args.alias[0]
        try:
            return {'add': self._add_recipes,
                    'remove': self._remove_recipes,
                    'update': self._update_recipes,
                    'list': self._list_recipes,
                   }[self.args.recipe_command]()
        except KeyError:
            self.log.error("Illegal recipes command: {}".format(self.args.recipe_command))
            return -1

    def _add_recipes(self):
        """
        Add recipe location:
        - If a prefix was explicitly selected, install it there
        - Otherwise, use local config file
        - Check alias is not already used
        """
        alias = self.args.alias
        uri = self.args.uri[0]
        self.log.debug("Preparing to add recipe location {name} -> {uri}".format(
            name=alias, uri=uri
        ))
        # Check recipe location alias is valid:
        if re.match(r'[a-z][a-z0-9_]*', alias) is None:
            self.log.error("Invalid recipe alias: {alias}".format(alias=alias))
            exit(1)
        if self.cfg.get_named_recipe_dirs().has_key(alias):
            if self.args.force:
                self.log.info("Overwriting existing recipe alias `{0}'".format(alias))
            elif not confirm("Alias `{0}' already exists, overwrite?".format(alias)):
                self.log.warn('Aborting.')
                return -1
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
        # Let the fetcher download the location
        self.log.debug("Fetching into directory: {0}/{1}".format(recipe_cache_top_level, alias))
        Fetcher().fetch_url(uri, recipe_cache_top_level, alias, {}) # No args
        # Write this to config file
        self.cfg.update_cfg_file({'recipes': {alias: uri}}, cfg_file=cfg_file)

    def _remove_recipes(self):
        """
        Remove a recipe alias and, if applicable, its cache.
        """
        if not self.cfg.get_named_recipe_dirs().has_key(self.args.alias):
            self.log.error("Unknown recipe alias: {alias}".format(alias=self.args.alias))
            return -1
        # Remove from config file
        cfg_file = self.cfg.get_named_recipe_cfg_file(self.args.alias)
        cfg_data = yaml.safe_load(open(cfg_file).read())
        cfg_data['recipes'].pop(self.args.alias, None)
        open(cfg_file, 'wb').write(yaml.dump(cfg_data, default_flow_style=False))
        recipe_cache_dir = os.path.join(
            os.path.split(cfg_file)[0],
            self.cfg.recipe_cache_dir,
            self.args.alias,
        )
        # If the recipe cache is not inside a PyBOMBS dir, don't delete it.
        if self.cfg.pybombs_dir not in recipe_cache_dir:
            return
        if os.path.exists(recipe_cache_dir):
            self.log.info("Removing directory: {cdir}".format(cdir=recipe_cache_dir))
            shutil.rmtree(recipe_cache_dir)

    def _update_recipes(self):
        """
        Update a remote recipe location.
        """
        try:
            uri = self.cfg.get_named_recipe_sources()[self.args.alias]
            recipes_dir = self.cfg.get_named_recipe_dirs()[self.args.alias]
        except KeyError:
            self.log.error("Error looking up recipe alias '{alias}'".format(alias=self.args.alias))
            return -1
        if not os.path.isdir(recipes_dir):
            self.log.error("Recipe location does not exist. Run `recipes add --force' to add recipes.")
            return -1
        cache_dir_top_level, cache_dir = os.path.split(os.path.normpath(recipes_dir))
        # Do actual update
        self.log.info("Updating recipe location `{alias}'...".format(alias=self.args.alias))
        if not Fetcher().update_src(uri, cache_dir_top_level, cache_dir, {}):
            self.log.error("Failed to update recipe location `{alias}'...".format(alias=self.args.alias))
            return -1

    def _list_recipes(self):
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
        format_installed_by = lambda x: [not_installed_string] if not x else x
        rows = []
        row_titles = {
            'id': "Package Name",
            'path': "Recipe Filename",
            'installed_by': "Installed By",
        }
        self.args.format = [x for x in self.args.format.split(",") if len(x)]
        if any(map(lambda x: x not in row_titles, self.args.format)):
            self.log.error("Invalid column formatting: {0}".format(self.args.format))
            return -1
        widths = {k: len(row_titles[k]) for k in row_titles.keys()}
        print("Loading package information...", end="")
        sys.stdout.flush()
        home_dir = os.path.expanduser("~")
        for pkg in all_recipes:
            if recipe.get_recipe(pkg, target=None).target != 'package':
                continue
            print(".", end="")
            sys.stdout.flush()
            row = {
                'id': pkg,
                'path': recmgr.get_recipe_filename(pkg).replace(home_dir, "~"),
                'installed_by': format_installed_by(pkgmgr.installed(pkg, return_pkgr_name=True)),
            }
            if self.args.in_prefix and 'source' not in row['installed_by']:
                continue
            if row['installed_by'] == [not_installed_string] and (self.args.installed or self.args.in_prefix):
                continue
            row['installed_by'] = ",".join(row['installed_by'])
            widths = {k: max(widths[k], len(row[k])) for k in row.iterkeys()}
            rows.append(row)
        print("\n")
        # Sort rows
        if self.args.sort_by is not None and self.args.sort_by in row_titles.keys():
            rows = sorted(rows, key=lambda k: k[self.args.sort_by])
        # Print Header
        hdr_len = 0
        for col_id in self.args.format:
            format_string = "{0:" + str(widths[col_id]) + "}  "
            hdr_title = format_string.format(row_titles[col_id])
            print(hdr_title, end="")
            hdr_len += len(hdr_title)
        print("")
        print("-" * hdr_len)
        # Print Table
        for row in rows:
            for col_id in self.args.format:
                format_string = "{{0:{width}}}  ".format(width=widths[col_id])
                print(format_string.format(row[col_id]), end="")
            print("")
        print("")

