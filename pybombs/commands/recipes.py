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
import ConfigParser
import shutil
from pybombs.commands import CommandBase
from pybombs.utils import subproc

class Recipes(CommandBase):
    """
    Manage recipe lists
    """
    cmds = {
        'recipes': 'Manage recipe lists',
    }
    remote_location_types = ('git', 'http')

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
            )
        def setup_subsubparser_update(parser):
            parser.add_argument(
                'alias',
                help="Name of recipe location to update",
            )
        ###### Start of setup_subparser()
        subparsers = parser.add_subparsers(
                help="Prefix Commands:",
                dest='prefix_command',
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
        if self.args.prefix_command == 'add':
            self._add_recipes()
        elif self.args.prefix_command == 'remove':
            self._remove_recipes()
        elif self.args.prefix_command == 'update':
            self._update_recipes()
        else:
            self.log.error("Illegal recipes command: {}".format(self.args.prefix_command))

    def _add_recipes(self):
        """
        Add recipe location:
        - If a prefix was explicitly selected, install it there
        - Otherwise, use local config file
        - Check alias is not already used
        """
        alias = self.args.alias[0]
        uri   = self.args.uri[0]
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
            recipe_cache = os.path.join(self.prefix.prefix_cfg_dir, self.cfg.recipe_cache_dir, alias)
        else:
            cfg_file = self.cfg.local_cfg
            recipe_cache = os.path.join(self.cfg.local_cfg_dir, self.cfg.recipe_cache_dir, alias)
        self.log.debug("Storing new recipe location to {cfg_file}".format(cfg_file=cfg_file))
        assert cfg_file is not None
        assert recipe_cache is not None
        # Detect recipe URI type
        uri_type = 'dir'
        for remote_type in self.remote_location_types: # If we're lucky, it starts with git+... or whatever
            if uri.find('{}+'.format(remote_type)) == 0:
                uri_type = remote_type
                uri = uri[len(remote_type)+1:]
        if uri_type == 'dir': # Then it might be an undeclared remote, let's guess:
            uri_mo = re.match(r'[a-z]+://', uri)
            if uri_mo is not None:
                uri_type = uri_mo.group(1)
                if not uri_type in self.remote_location_types:
                    self.log.error("Unrecognized remote recipe URL: {url}".format(
                        uri
                    ))
                    exit(1)
        if uri_type != 'dir':
            uri = "{proto}+{url}".format(proto=uri_type, url=uri)
        # Write this to config file
        cfg_parser = ConfigParser.ConfigParser()
        cfg_parser.read(cfg_file)
        recipe_section_name = 'recipes'
        if not cfg_parser.has_section(recipe_section_name):
            cfg_parser.add_section(recipe_section_name)
        cfg_parser.set(recipe_section_name, alias, uri)
        cfg_parser.write(open(cfg_file, 'wb'))
        if uri_type == 'dir':
            return
        # Now make sure we don't already have a cache dir
        if os.path.isdir(recipe_cache):
            self.log.warn("Cache dir {cdir} for remote recipe location {alias} already exists! Deleting.".format(
                cdir=recipe_cache, alias=alias
            ))
            shutil.rmtree(recipe_cache)
        # All's ready now, so let's download
        self._update_recipes(uri, recipe_cache)

    def _remove_recipes(self):
        pass

    def _update_recipes(self, uri=None, target_dir=None):
        """
        Update a remote recipe location. A remote recipe location
        may still be uninitialized at this point (e.g. a git repo
        might not have been cloned yet).
        """
        if uri is None:
            try:
                uri = self.cfg.get_named_recipe_locations()[self.args.alias]
            except KeyError:
                self.log.error("Error looking up recipe alias '{alias}'".format(alias=self.args.alias))
                exit(1)
        if target_dir is None:
            target_dir = os.path.join(
                os.path.split(self.cfg.get_named_recipe_source(self.args.alias))[0],
                    self.cfg.recipe_cache_dir,
                    self.args.alias
            )
        # If this is local, we need to do nothing
        if not any([uri.find('{proto}+'.format(proto=x)) for x in self.remote_location_types]):
            self.log.info("Local recipe directories can't be updated through PyBOMBS.")
            return
        # Make sure the top cache dir exists (e.g. ~/.pybombs/recipes)
        if not os.path.isdir(os.path.split(target_dir)[0]):
            os.mkdir(os.path.split(target_dir)[0])
        protocol, uri = uri.split('+', 1)
        # Do actual update
        update_callback = {
            'git': self._update_recipes_git,
        }
        self.log.info("Updating recipe location '{alias}'...".format(alias=self.args.alias))
        update_callback[protocol](uri, target_dir)

    def _update_recipes_git(self, url, target_dir):
        """
        Update a recipe URL that's in a git repo
        """
        if os.path.isdir(target_dir):
            os.chdir(target_dir)
            subproc.monitor_process(['git', 'pull', '--rebase'])
        else:
            target_dir_base, target_dir_top = os.path.split(target_dir)
            os.chdir(target_dir_base)
            subproc.monitor_process(['git', 'clone', '--depth=1', url, target_dir_top])

