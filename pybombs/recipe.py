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
"""
Recipe representation class.
"""

import re
import os
import shlex
from io import StringIO
from six import iteritems

from pybombs import pb_logging
from pybombs import recipe_manager
from pybombs import config_manager
from pybombs.pb_exception import PBException
from pybombs.config_file import PBConfigFile
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

class PBPackageRequirementScanner(object):
    """
    Turns a package requirement string (something like
    libfoo >= 2.0 && libbar >= 3.0) into a PBPackageRequirement(Pair).
    """
    ### Tokens => Functors
    # Token matching is simple: If the key is a string, it must match. If it's
    # a tuple, the token must be an element. If it's a regular expression
    # MatchObject, it has to match().
    lexicon = {
        # Package name
        re.compile(r'[a-zA-Z-][a-zA-Z0-9./+_-]+'): lambda s, tok: s.pl_pkg(tok),
        # Version
        re.compile(r'[0-9]+[0-9.]*'): lambda s, tok: s.pl_ver(tok),
        # Open parens
        '(': lambda s, tok: s.pl_lpar(tok),
        # Close parens
        ')': lambda s, tok: s.pl_rpar(tok),
        # Comparators
        ('>=', '<=', '==', '!='): lambda s, tok: s.pl_cmp(tok),
        # Combiners
        ('&&', '||'): lambda s, tok: s.pl_cmb(tok),
    }

    def __init__(self, req_string):
        self.log = pb_logging.logger.getChild("ReqScanner")
        self.preq = None
        self.stack = []
        if not req_string:
            self.log.obnoxious("Empty requirements string.")
            return
        lexer = shlex.shlex(req_string)
        lexer.wordchars += '-<>=.&|/'
        while True:
            token = lexer.get_token()
            if token == lexer.eof:
                self.end_distro_pkg_expr()
                break
            self.get_token_functor(token)(self, token)
        self.log.obnoxious("Done parsing requirements string `{0}`".format(req_string))

    def get_token_functor(self, token):
        " Return a functor for a given token or throw "
        for (match, functor) in self.lexicon.items():
            if isinstance(match, str) and token == match:
                return functor
            if isinstance(match, tuple) and token in match:
                return functor
            if hasattr(match, 'match') and match.match(token):
                return functor
        raise PBException("Invalid token: {tok}".format(token))

    def pl_pkg(self, pkg_name):
        " Called in a package requirements list, when a package name is found "
        if self.preq is None:
            self.log.obnoxious("Adding package with name {}".format(pkg_name))
            self.preq = PBPackageRequirement(pkg_name)
        elif isinstance(self.preq, PBPackageRequirement):
            if self.preq.compare is None:
                self.preq.name = " ".join((self.preq.name, pkg_name))
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
                    raise PBException("Parsing Error. Did not expect package name here ({0}).".format(self.preq.second))
        else:
            raise PBException("Random Foobar Parsing Error.")

    def pl_lpar(self, par):
        " Called in a package requirements list, when lparens are found "
        assert par == "("
        self.stack.append(self.preq)
        self.preq = None

    def pl_rpar(self, par):
        " Called in a package requirements list, when rparens are found "
        assert par == ")"
        prev = self.stack.pop()
        if prev is not None:
            prev.second = self.preq
            self.preq = prev

    def pl_cmp(self, cmpr):
        " Called in a package requirements list, when version comparator is found "
        self.log.obnoxious("Adding version comparator {}".format(cmpr))
        if isinstance(self.preq, PBPackageRequirement):
            self.preq.compare = cmpr
        else:
            self.preq.second.compare = cmpr

    def pl_ver(self, ver):
        " Called in a package requirements list, when version number is found "
        self.log.obnoxious("Adding version number {}".format(ver))
        if isinstance(self.preq, PBPackageRequirement):
            self.preq.version = ver
        else:
            self.preq.second.version = ver

    def pl_cmb(self, cmb):
        " Called in a package requirements list, when a logical combiner (||, &&) is found "
        self.log.obnoxious("Found package combiner {}".format(cmb))
        if self.preq is None:
            raise PBException("Parsing Error. Did not expect combiner here.")
        self.preq = PBPackageRequirementPair(self.preq)
        self.preq.combiner = cmb

    def end_distro_pkg_expr(self):
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
        self._data = self._load_recipe_from_file(filename)
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
            parent_data = self._load_recipe_from_file(filename)
            self._data['depends'] = self._data['depends'] + parent_data['depends']
            self._data = dict_merge(parent_data, self._data)
            self._data['inherit'] = parent_data.get('inherit')
        if self._data.get('target') == 'package':
            self._data = self.get_local_package_data()
        else:
            self._data = self._normalize_package_data(self._data)
        # Map all recipe info onto self:
        for k, v in iteritems(self._data):
            if not hasattr(self, k):
                setattr(self, k, v)
        self.log.obnoxious("Loaded recipe - {}".format(self.id))

    def __str__(self):
        import yaml
        out = "Recipe: {id}\n".format(id=str(self.id))
        out += yaml.dump(self._data, default_flow_style=False)
        return out

    def _load_recipe_from_file(self, filename):
        """
        Turn a .lwr file into a valid recipe datastructure.
        """
        data = PBConfigFile(filename).get()
        # Make sure dependencies is always a valid list:
        if 'depends' in data and data['depends'] is not None:
            if not isinstance(data['depends'], list):
                data['depends'] = [data['depends'], ]
        else:
            data['depends'] = []
        return data

    def _normalize_package_data(self, package_data_dict):
        """
        Make sure the package data follows certain rules.
        """
        if 'source' in package_data_dict and not isinstance(package_data_dict['source'], list):
            package_data_dict['source'] = [package_data_dict['source'],]
        return package_data_dict

    def get_dict(self):
        """
        Return recipe data as dictionary.
        r.get_dict()['foo'] is the same as r.foo.
        """
        return self._normalize_package_data(self._data)

    def get_package_reqs(self, pkg_type):
        """
        Return a PBPackageRequirement(Pair) object for the selected
        pkg_type. E.g., if pkg_type is 'deb', you can use this to
        figure out which .deb packages to install.

        If pkg_type was not listed in the recipe, return None.
        """
        req_string = getattr(self, 'satisfy', {}).get(pkg_type)
        if req_string is True:
            return req_string
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
        def var_replace(mo, var_dict, cfg):
            """
            Expects arguments to be matchobjects for strings starting with $.
            Returns the variable replacement value.
            """
            var_name_dollar = mo.group(0)
            assert len(var_name_dollar) > 1 and var_name_dollar[0] == '$'
            var_name = var_name_dollar[1:] # Strip $
            if var_name == 'prefix':
                return cfg.get_active_prefix().prefix_dir
            if var_name == 'src_dir':
                return cfg.get_active_prefix().src_dir
            if var_name in var_dict:
                return var_dict.get(var_name)
            try:
                return str(cfg.get(var_name))
            except PBException as ex:
                raise PBException("Could not expand variable {0}.".format(var_name_dollar))
        ###
        # Starts with a $, unless preceded by \
        var_re = re.compile(r'(?<!\\)\$[a-z][a-z0-9_]*')
        var_repl = lambda mo: var_replace(mo, self.vars, config_manager.config_manager)
        try:
            (s, n_subs) = var_re.subn(var_repl, s)
        except PBException as ex:
            self.log.error("Error parsing {s}: {e}".format(s=s, e=str(ex)))
            raise ex
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
        return self._normalize_package_data(dict_merge(
            self.get_dict(),
            config_manager.config_manager.get_package_flags(
                self.id, self.get_dict().get('category')
            )
        ))


recipe_cache = {}
def get_recipe(pkgname, target='package', fail_easy=False):
    """
    Return a recipe object by its package name.
    """
    cache_key = pkgname
    if cache_key in recipe_cache:
        pb_logging.logger.getChild("get_recipe").obnoxious("Woohoo, this one's already cached ({})".format(pkgname))
        return recipe_cache[cache_key]
    try:
        r = Recipe(recipe_manager.recipe_manager.get_recipe_filename(pkgname))
    except PBException as ex:
        if fail_easy:
            return None
        else:
            pb_logging.logger.getChild("get_recipe").error("Error fetching recipe `{0}':\n{1}".format(
                pkgname, str(ex)
            ))
            raise ex
    recipe_cache[cache_key] = r
    if target is not None and r.target != target:
        if fail_easy:
            return None
        pb_logging.logger.getChild("get_recipe").error("Recipe for `{pkg}' found, but does not match request target type `{req}' (is `{actual}').".format(
            pkg=pkgname, req=target, actual=r.target
        ))
        raise PBException("Recipe has wrong target type.")
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
