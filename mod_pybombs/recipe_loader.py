#!/usr/bin/env python
#
# Copyright 2013 Tim O'Shea
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

import os,re,sys
from recipe import *;

def load_all():
    global_recipes.clear();
    files = os.listdir("recipes");
    recipes = [];
    print "Loading recipes ..."
    for f in files:
        if(re.match("[\w\d_-]+.lwr$", f)):
            recipes.append(f[:-4]);

    for r in recipes:
        if not global_recipes.has_key(r):
            try:
                global_recipes[r] = recipe(r);
            except:
                print "Failed to load recipe", r
            
    global_recipes['all'] = recipe('all')
    global_recipes['all'].category = "pseudo"
    global_recipes['all'].depends.extend(recipes)

    print "Loading recipes ... done"
    

    


