#!/usr/bin/env python2
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
"""
Recipe Manager: Handles the available recipes
"""

import os
import recipe
import pb_logging

class RecipeListManager(object):
    """
    Handles lists of recipes.
    This will handle multiple sets of recipes by means of a
    recipe hierarchy.

    Recipe lists get different ranks. From least to most important:
    - Global default recipe list (defined in /etc/pybombs.d/config.dat or something like that)
    - Whatever is defined in ~/.pybombs/config.dat
    - The selected prefixes recipe list (either an actual recipe folder
      in the prefix, or a value set in that prefix' config.dat)
    - The dir set in env variable PYBOMBS_RECIPE_DIR
    - Dir given through command line (-r)
    """
    def __init__(self):
        self.log = pb_logging.logger.getChild("RecipeListManager")
        self._recipe_list = {}
        self._append_dir('/home/mbr0wn/src/pybombs/recipes')
        self._append_dir('/home/mbr0wn/src/pybombs/recipes2')


    # TODO not sure if we want to keep this
    #def list(self):
        #"""
        #Returns a list of all recipes, sorted by category.

        #The return value is a dict with the following format:
        #{
            #categoryname1: [list of recipe names],
            #categoryname2: [list of recipe names],
        #}
        #"""
        #pass

    def get_recipe_filename(self, name):
        """
        Return the filename of the .lwr file that contains the recipe
        for package called 'name'.
        """
        return self._recipe_list[name][0]


    def _append_dir(self, dirname):
        """
        Goes through directory 'dirname' and looks at all .lwr files.
        Adds a list of tuples (pkgname, filename) to the internal
        recipe cache.
        """
        if not os.path.isdir(dirname):
            self.log.error("'{0}' is not a directory.".format(dirname))
            return
        self.log.debug("Scanning directory '{0}' for recipes...".format(dirname))
        # Return list of .lwr files from this dir:
        lwr_files = [f for f in os.listdir(dirname) if os.path.splitext(f)[1] == '.lwr']
        self.log.debug("Found {0} new recipes.".format(len(lwr_files)))
        for f in lwr_files:
            pkgname = os.path.splitext(f)[0]
            abs_filename = os.path.join(dirname, f)
            if pkgname in self._recipe_list.keys():
                self._recipe_list[pkgname].insert(0, abs_filename)
            else:
                self._recipe_list[pkgname] = [abs_filename,]


if __name__ == "__main__":
    rlm = RecipeListManager()
    print rlm.get_recipe_filename("gr-specest")

