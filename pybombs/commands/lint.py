#
# Copyright 2015 Free Software Foundation, Inc.
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
""" PyBOMBS command: lint """

from __future__ import print_function
import os
from six import iteritems
from pybombs.commands import CommandBase
from pybombs.config_file import PBConfigFile
from pybombs import recipe
from pybombs.pb_exception import PBException

class Lint(CommandBase):
    """ Lint """
    cmds = {
        'lint': 'Lint a prefix or recipe',
    }

    @staticmethod
    def setup_subparser(parser, cmd=None):
        """
        Set up a subparser for 'lint'
        """
        parser.add_argument(
            'target', type=str, default=None, nargs='?',
            help="Recipe file or prefix",
        )

    def __init__(self, cmd, args):
        CommandBase.__init__(self,
            cmd, args,
            require_prefix=False,
        )

    def run(self):
        """ Go, go, go! """
        if self.args.target is None:
            if self.prefix is not None:
                return self._lint_prefix(self.prefix.prefix_dir)
            self.log.error("No linting target specified.")
            return 1
        if self.prefix is not None and self.args.target in self.prefix.prefix_aliases:
            return self._lint_prefix(self.prefix.prefix_aliases[self.args.target])
        elif os.path.isfile(self.args.target):
            return self._lint_recipe(self.args.target)
        elif os.path.isdir(self.args.target):
            return self._lint_prefix(self.args.target)
        if os.path.splitext(self.args.target)[1].lower() == '.lwr':
            print("I think I'm supposed to lint a recipe, but can't open one.")
        else:
            self.log.error("Don't know what I'm supposed to lint")

    def _lint_prefix(self, prefix_dir):
        """
        Perform these checks on a prefix:
        - See if config dir exists
        - See if inventory file exists
        - Check entries in inventory and compare with available source
          directories
        """
        self.cfg.load(prefix_dir)
        prefix = self.cfg.get_active_prefix()
        print("Linting prefix: `{0}'".format(prefix.prefix_dir))
        if prefix.src_dir is None or not os.path.isdir(prefix.src_dir):
            print("[HMM] - No source dir")
        if prefix.prefix_cfg_dir is None or not os.path.isdir(prefix.prefix_cfg_dir):
            print("[BAD] - No config dir")
        if prefix.inventory is None:
            print("[HMM] - No inventory")

    def _lint_recipe(self, recipe_file):
        """
        Check if recipe_file is a valid recipe
        """
        print("Linting recipe `{0}'".format(recipe_file))
        # Basic file checks
        try:
            recipe_dict = PBConfigFile(recipe_file).get()
        except IOError:
            self.log.error("Can't open `{0}'".format(recipe_file))
            return -1
        except AttributeError:
            self.log.error("Can't parse contents of file `{0}'".format(recipe_file))
            return -1
        if not isinstance(recipe_dict, dict):
            self.log.error("Invalid recipe file. Not a dict.")
            return -1
        # Try loading as recipe
        try:
            rec = recipe.Recipe(recipe_file)
            if not hasattr(rec, 'satisfy'):
                print("[HMM] - No satisfy rules declared")
            else:
                for pkgtype in rec.satisfy.keys():
                    rec.get_package_reqs(pkgtype)
        except PBException as ex:
            print("[VERY BAD] - Recipe error: " + str(ex))
        # Check keys
        key_check = {
            'HMM': ['source', 'depends'],
            'BAD': ['inherit', 'category'],
        }
        for err_type, key_list in iteritems(key_check):
            for key in key_list:
                if not key in recipe_dict:
                    print("[{err}] Recipe doesn't have key: {key}".format(err=err_type, key=key))

