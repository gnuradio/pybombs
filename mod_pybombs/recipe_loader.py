#!/usr/bin/env python
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
            global_recipes[r] = recipe(r);
            
    global_recipes['all'] = recipe('all')
    global_recipes['all'].category = "pseudo"
    global_recipes['all'].depends.extend(recipes)

    print "Loading recipes ... done"
    

    


