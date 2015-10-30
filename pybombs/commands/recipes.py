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

import re
import os
import shutil
import yaml
from pybombs.commands import CommandBase
from pybombs.utils import subproc
from pybombs.fetcher import Fetcher

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
        ###### Start of setup_subparser()
        subparsers = parser.add_subparsers(
                help="Recipe Commands:",
                dest='recipe_command',
        )
        recipes_cmd_name_list = {
            'add':    ('Add a new recipes location.', setup_subsubparser_add),
            'remove': ('Remove a recipes location.', setup_subsubparser_remove),
            'update': ('Update recipes with a remote repository', setup_subsubparser_update),
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
                require_inventory=False
        )

    def run(self):
        """ Go, go, go! """
        self.args.alias = self.args.alias[0]
        if self.args.recipe_command == 'add':
            self._add_recipes()
        elif self.args.recipe_command == 'remove':
            self._remove_recipes()
        elif self.args.recipe_command == 'update':
            self._update_recipes()
        else:
            self.log.error("Illegal recipes command: {}".format(self.args.recipe_command))

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
        if self.cfg.get_named_recipe_locations().has_key(alias):
            if not self.args.force:
                self.log.error("Recipe name {alias} is already taken!".format(alias=alias))
                exit(1)
        # Determine where to store this new recipe location:
        store_to_prefix = False
        if self.prefix is not None and self.prefix.prefix_src in ("cli", "cwd"):
            store_to_prefix = True
        cfg_file = None
        recipe_cache = None
        if store_to_prefix:
            cfg_file = self.prefix.cfg_file
            recipe_cache_top_level = os.path.join(self.prefix.prefix_cfg_dir, self.cfg.recipe_cache_dir)
        else:
            cfg_file = self.cfg.local_cfg
            recipe_cache_top_level = os.path.join(self.cfg.local_cfg_dir, self.cfg.recipe_cache_dir)
        recipe_cache = os.path.join(recipe_cache_top_level, alias)
        self.log.debug("Storing new recipe location to {cfg_file}".format(cfg_file=cfg_file))
        assert cfg_file is not None
        assert recipe_cache_top_level is not None
        assert recipe_cache is not None
        assert alias
        # Now make sure we don't already have a cache dir
        if os.path.isdir(recipe_cache):
            self.log.warn("Cache dir {cdir} for remote recipe location {alias} already exists! Deleting.".format(
                cdir=recipe_cache, alias=alias
            ))
            shutil.rmtree(recipe_cache)
        # Write this to config file
        cfg_data = yaml.safe_load(open(cfg_file).read())
        if not cfg_data.has_key('recipes'):
            cfg_data['recipes'] = {}
        cfg_data['recipes'][alias] = uri
        open(cfg_file, 'wb').write(yaml.dump(cfg_data, default_flow_style=False))
        # Let the fetcher download the location
        self.log.debug("Cloning into directory: {0}/{1}".format(recipe_cache_top_level, alias))
        Fetcher().fetch_url(uri, recipe_cache_top_level, alias, {}) # No args

    def _remove_recipes(self):
        """
        Remove a recipe alias and, if applicable, its cache.
        """
        if not self.cfg.get_named_recipe_locations().has_key(self.args.alias):
            self.log.error("Unknown recipe alias: {alias}".format(alias=self.args.alias))
            exit(1)
        # Remove from config file
        cfg_file = self.cfg.get_named_recipe_source(self.args.alias)
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
            uri = self.cfg.get_named_recipe_locations()[self.args.alias]
        except KeyError:
            self.log.error("Error looking up recipe alias '{alias}'".format(alias=self.args.alias))
            exit(1)
        target_dir_top_level = os.path.join(
            os.path.split(self.cfg.get_named_recipe_source(self.args.alias))[0],
            self.cfg.recipe_cache_dir,
        )
        if not os.path.isdir(os.path.join(target_dir_top_level, self.args.alias)):
            self.log.error("Recipe location does not exist. Run `recipes add --force' to add recipes.")
            exit(1)
        # Do actual update
        self.log.info("Updating recipe location '{alias}'...".format(alias=self.args.alias))
        Fetcher().update_src(uri, target_dir_top_level, self.args.alias, {})

