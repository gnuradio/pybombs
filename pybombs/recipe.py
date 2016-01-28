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
"""
Recipe representation class.
"""

import re
import os
import yaml
import StringIO
from plex import *

from pybombs import pb_logging
from pybombs import recipe_manager
from pybombs import config_manager
from pybombs.pb_exception import PBException
from pybombs.utils import dict_merge

class PBPackageRequirement(object):
    """
    Store info on a dependency package:
    - Package name (typically deb or rpm or something like that)
    - Version + Comparator
    """
    def __init__(self, name):
        self.name = name
        self.compare = None
        self.version = None

    def ev(self, func):
        """
        Run func() with this requirement
        """
        return func(self.name, self.compare or ">=", self.version)

    def __str__(self, lvl=0):
        return " "*lvl + "PackageRequirement({}, {}, {})".format(self.name, self.compare, self.version)


class PBPackageRequirementPair(object):
    """
    Joining logic for multiple dep packages (rpms, debs, etc.)
    """
    def __init__(self, pkg):
        self.first = pkg
        self.second = None
        self.combiner = None

    def ev(self, func):
        if self.combiner is None or self.second is None:
            return self.first.ev(func)
        elif self.combiner == "&&":
            return self.first.ev(func) and self.second.ev(func)
        elif self.combiner == "||":
            return self.first.ev(func) or self.second.ev(func)

    def __str__(self, lvl=0):
        a = " "*lvl + "PBPackageRequirementPair: ({})\n".format(self.combiner)
        a = a + " "*lvl + self.first.__str__(1) + "\n"
        if(self.second):
            a = a + " "*lvl + self.second.__str__(1)
        else:
            a = a + " "*lvl + "None"
        return a

class PBPackageRequirementScanner(Scanner):
    """
    Turns a package requirement string (something like
    libfoo >= 2.0 && libbar >= 3.0) into a PBPackageRequirement(Pair).
    """
    ### Plex: Patterns
    letter      = Range("AZaz")
    digit       = Range("09")
    pkgname     = Rep1(letter | Str("-")) + Rep(letter | digit | Any("-.+_"))
    space       = Any(" \t\n")
    rspace      = Rep(space)
    lpar        = Str("(")
    rpar        = Str(")")
    comparators = Str(">=") | Str("<=") | Str("==") | Str("!=")
    combiner    = Str('&&') | Str('||')
    version     = Rep(digit) + Rep(Str(".") + Rep(digit))

    def __init__(self, req_string):
        self.log = pb_logging.logger.getChild("ReqScanner")
        self.preq = None
        if not req_string:
            self.log.obnoxious("Empty requirements string.")
            return
        lexicon = Lexicon([
            (self.rspace, IGNORE),
            (self.pkgname, self.pl_pkg),
            (self.version, self.pl_ver),
            (self.lpar, self.pl_lpar),
            (self.rpar, self.pl_rpar),
            (self.comparators, self.pl_cmp),
            (self.combiner, self.pl_cmb),
            (Eol, self.end_distro_pkg_expr),
        ])
        fileobj = StringIO.StringIO(req_string)
        self.stack = []
        Scanner.__init__(self, lexicon, fileobj, "ReqString")
        self.log.debug("Parsing '{rs}'".format(rs=req_string))
        Scanner.read(self)
        fileobj.close()
        self.log.obnoxious("Done Parsing.")

    def pl_pkg(self, scanner, pkg_name):
        " Called in a package requirements list, when a package name is found "
        if self.preq is None:
            self.log.obnoxious("Adding package with name {}".format(pkg_name))
            self.preq = PBPackageRequirement(pkg_name)
        elif isinstance(self.preq, PBPackageRequirement):
            if self.preq.compare is None:
                self.preq.name =  " ".join((self.preq.name, pkg_name))
                self.log.obnoxious("Extending package name {}".format(self.preq.name))
            else:
                raise PBException("Parsing Error. Did not expect package name here.")
        elif isinstance(self.preq, PBPackageRequirementPair):
            if self.preq.second is None:
                self.log.obnoxious("Adding package with name {}".format(pkg_name))
                self.preq.second = PBPackageRequirement(pkg_name)
            else:
                if self.preq.second.compare is None:
                    self.preq.second.name = " ".join((self.preq.second.name, pkg_name))
                    self.log.obnoxious("Extending package name {}".format(self.preq.second.name))
                else:
                    print(str(self.preq.second))
                    raise PBException("Parsing Error. Did not expect package name here.")
        else:
            raise PBException("Random Foobar Parsing Error.")

    def pl_lpar(self, scanner, par):
        " Called in a package requirements list, when lparens are found "
        self.stack.append(self.preq)
        self.preq = None

    def pl_rpar(self, scanner, par):
        " Called in a package requirements list, when rparens are found "
        prev = self.stack.pop()
        if prev is not None:
            prev.second = self.preq
            self.preq = prev

    def pl_cmp(self, scanner, cmpr):
        " Called in a package requirements list, when version comparator is found "
        self.log.obnoxious("Adding version comparator {}".format(cmpr))
        if isinstance(self.preq, PBPackageRequirement):
            self.preq.compare = cmpr
        else:
            self.preq.second.compare = cmpr

    def pl_ver(self, scanner, ver):
        " Called in a package requirements list, when version number is found "
        self.log.obnoxious("Adding version number {}".format(ver))
        if isinstance(self.preq, PBPackageRequirement):
            self.preq.version = ver
        else:
            self.preq.second.version = ver

    def pl_cmb(self, scanner, cmb):
        " Called in a package requirements list, when a logical combiner (||, &&) is found "
        self.log.obnoxious("Found package combiner {}".format(cmb))
        if self.preq is None:
            raise PBException("Parsing Error. Did not expect combiner here.")
        self.preq = PBPackageRequirementPair(self.preq)
        self.preq.combiner = cmb

    def end_distro_pkg_expr(self, scanner, e):
        " Called when a list of package reqs is finished "
        self.log.obnoxious("End of requirements list")
        self.stack = []
        return "foo"

    def get_preq(self):
        " Return result, or None for no requirements. "
        return self.preq

class Recipe(object):
    """
    Object representation of a recipe file.
    """
    def __init__(self, filename):
        self.id = os.path.splitext(os.path.basename(filename))[0]
        self.log = pb_logging.logger.getChild("Recipe[{}]".format(self.id))
        self.inherit = 'empty'
        self._static = False
        # Load original recipe:
        self.log.obnoxious("Loading recipe file: {}".format(filename))
        self._data = self._load_recipe_from_yaml(filename)
        # Recursively do the inheritance:
        while self._data.get('inherit', 'empty'):
            inherit_from = self._data.get('inherit', 'empty')
            try:
                filename = recipe_manager.recipe_manager.get_template_filename(inherit_from)
                self.log.obnoxious("Loading template file: {}".format(filename))
            except PBException as e:
                self.log.warn("Recipe attempting to inherit from unknown template {}".format(
                    inherit_from
                ))
                break
            self.log.obnoxious("Inheriting from file {}".format(filename))
            parent_data = self._load_recipe_from_yaml(filename)
            self._data['depends'] = self._data['depends'] + parent_data['depends']
            self._data = dict_merge(parent_data, self._data)
            self._data['inherit'] = parent_data.get('inherit')
        # Post-process some fields:
        if self._data.has_key('source') and not isinstance(self._data['source'], list):
            self._data['source'] = [self._data['source'],]
        # Package flags override vars:
        self._data['vars'] = dict_merge(
            self._data.get('vars', {}),
            config_manager.config_manager.get_package_flags(
                self.id, self._data.get('category')
            ).get('vars', {})
        )
        # Map all recipe info onto self:
        for k, v in self._data.iteritems():
            if not hasattr(self, k):
                setattr(self, k, v)
        self.log.obnoxious("Loaded recipe - {}".format(self))



    def __str__(self):
        out = "Recipe: {id}\n".format(id=str(self.id))
        out += yaml.dump(self._data)
        return out

    def _load_recipe_from_yaml(self, filename):
        """
        Turn a YAML file into a valid recipe datastructure.
        """
        data = yaml.safe_load(open(filename).read())
        # Make sure dependencies is always a valid list:
        if data.has_key('depends') and data['depends'] is not None:
            if not isinstance(data['depends'], list):
                data['depends'] = [data['depends'], ]
        else:
            data['depends'] = []
        return data

    def get_dict(self):
        """
        Return recipe data as dictionary.
        r.get_dict()['foo'] is the same as r.foo.
        """
        return self._data

    def get_package_reqs(self, pkg_type):
        """
        Return a PBPackageRequirement(Pair) object for the selected
        pkg_type. E.g., if pkg_type is 'deb', you can use this to
        figure out which .deb packages to install.

        If pkg_type was not listed in the recipe, return None.
        """
        req_string = getattr(self, 'satisfy', {}).get(pkg_type)
        return PBPackageRequirementScanner(req_string).get_preq()

    def set_static(self, static):
        """
        Set the internal build choice to static or not.
        """
        self._static = bool(static)

    def get_command(self, cmd, static=None):
        """
        Return a recipe option that can exists both as a static version
        and a regular one. Example:
        >>> pm.get_command('configure', True)
        cmake ...

        This will return configure_static, if that exists, or configure if not,
        and None if neither exist.

        If static is not provided, it will use the state set by set_static().
        """
        if static is None:
            static = self._static
        if static and hasattr(self, '{cmd}_static'.format(cmd=cmd)):
            return getattr(self, '{cmd}_static'.format(cmd=cmd))
        return getattr(self, cmd, None)

    def var_replace_all(self, s):
        """
        Replace all the $variables in string 's' with the vars
        from 'recipe'. If keys are not in vars, try config options.
        Default to empty strings.
        """
        # PyBOMBS1 supported a conditional replacement mechanism,
        # where variable==FOO?{a}:{b} would return a if variables
        # matches FOO, or b otherwise. We'll leave this out for now.
        def var_replace(mo, vars, cfg):
            """
            Expects arguments to be matchobjects for strings starting with $.
            Returns the variable replacement value.
            """
            var_name = mo.group(0)
            assert len(var_name) > 1 and var_name[0] == '$'
            var_name = var_name[1:] # Strip $
            if var_name == 'prefix':
                return cfg.get_active_prefix().prefix_dir
            if var_name == 'src_dir':
                return cfg.get_active_prefix().src_dir
            return vars.get(var_name, str(cfg.get(var_name, '')))
        ###
        # Starts with a $, unless preceded by \
        var_re = re.compile(r'(?<!\\)\$[a-z][a-z0-9_]*')
        var_repl = lambda mo: var_replace(mo, self.vars, config_manager.config_manager)
        (s, n_subs) = var_re.subn(var_repl, s)
        if n_subs == 0:
            return s
        return self.var_replace_all(s)

    def get_local_package_data(self):
        """
        Merges the recipe data with local config settings. Local settings
        always supersede recipe settings.

        This allows users to override anything in a recipe with whatever's stored
        in the `package:` and `category:` sections of their local config files.
        """
        return dict_merge(
            self.get_dict(),
            config_manager.config_manager.get_package_flags(
                self.id, self.get_dict().get('category')
            )
        )


recipe_cache = {}
def get_recipe(pkgname, target='package', fail_easy=False):
    """
    Return a recipe object by its package name.
    """
    cache_key = pkgname
    if recipe_cache.has_key(cache_key):
        pb_logging.logger.getChild("get_recipe").obnoxious("Woohoo, this one's already cached ({})".format(pkgname))
        return recipe_cache[cache_key]
    r = Recipe(recipe_manager.recipe_manager.get_recipe_filename(pkgname))
    recipe_cache[cache_key] = r
    if target is not None and r.target != target:
        if fail_easy:
            return None
        pb_logging.logger.getChild("get_recipe").error("Recipe for `{pkg}' found, but does not match request target type `{req}' (is `{actual}').".format(
            pkg=pkgname, req=target, actual=r.target
        ))
        exit(1)
    return r


if __name__ == "__main__":
    #recipe_filename = '/home/mbr0wn/src/pybombs/recipes/gr-specest.lwr'
    #recipe_filename = '/home/mbr0wn/src/pybombs/recipes/python.lwr'
    recipe_filename = '/home/mbr0wn/src/pybombs/recipes/gnuradio.lwr'
    #pb_logging.logger.setLevel(1)
    #scanner = Recipe(recipe_filename)
    #for k, v in scanner.satisfy.iteritems():
        #print "{}:".format(k)
        #print str(v)
    #print scanner.lvars
