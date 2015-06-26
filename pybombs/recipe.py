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
Recipe representation class.
"""

import os
import re
import copy

from pybombs import pb_logging
from pybombs import recipe_manager
from pybombs.pb_exception import PBException

from plex import *


# structure for a dependency package (name, comparator, version) (for rpm or deb)
class PBPackageRequirement(object):
    def __init__(self, name):
        self.name = name
        self.compare = None
        self.version = None

    def ev(self, func):
        return func(self.name, self.compare, self.version)

    def __str__(self, lvl=0):
        return " "*lvl + "PackageRequirement({}, {}, {})".format(self.name, self.compare, self.version)


# joining logic for multiple dep packages (for rpms and debs)
class PBPackageRequirementPair(object):
    def __init__(self, pkg):
        self.first = pkg
        self.second = None
        self.combiner = None

    def ev(self, func):
        if self.combiner == "&&":
            return self.first.ev(func) and self.second.ev(func)
        elif self.combiner == "||":
            return self.first.ev(func) or self.second.ev(func)

    def __str__(self, lvl=0):
        a = " "*lvl + "PBPackageRequirementPair: (%s)"%(self.combiner) + "\n"
        a = a + " "*lvl + self.first.__str__(1) + "\n"
        if(self.second):
            a = a + " "*lvl + self.second.__str__(1)
        else:
            a = a + " "*lvl + "None"
        return a


class Recipe(Scanner):
    """
    Represents a recipe. Internally, it's a lexical scanner for the actual
    recipe.
    """
    def __init__(self, filename, lvars=None, static=False):
        self.id = os.path.splitext(os.path.basename(filename))[0]
        self.log = pb_logging.logger.getChild("Recipe[{}]".format(self.id))
        self.static = static
        self.deps = []
        self.srcs = []
        self.satisfy_deb = {}
        self.install_like = None
        self.category = None
        self.satisfy = {}
        self.src_configure = ""
        self.src_make = ""
        self.src_install = ""
        self.src_verify = ""
        self.src_uninstall = ""
        self.configuredir = ""
        self.makedir = ""
        self.install_dir = ""
        self.git_branch = "master"
        self.git_args = ""
        self.svn_rev = "HEAD"
        self.git_rev = ""
        self.currpkg = None
        self.pkgstack = []
        self.curr_pkg_type = None
        self.varname = None
        self.varoverride = False
        self.var = {}
        # Init lvars:
        self.lvars = {}
        if lvars is not None:
            self.lvars = copy.copy(lvars)
        # Init recipe scanner:
        if not os.path.exists(filename):
            self.log.error("No such recipe file: {}".format(filename))
            exit(1)
        recipe_file = open(filename, 'r')
        Scanner.__init__(self, self.lexicon, recipe_file, filename)
        # Put scanner into default state:
        self.begin("")
        self.log.debug("Parsing {}".format(filename))
        while True:
            token = Scanner.read(self)
            if token[0] is None:
                break
        recipe_file.close()
        self.log.debug("Done Parsing.")

    def set_attr(self, arg, key):
        " Set a simple attribute "
        self.log.log(1, "Setting attribute {} = {}".format(key, arg))
        setattr(self, key, arg)

    def mainstate(self, a):
        " Reset to default state "
        self.begin("")

    def deplist_add(self, pkg):
        " Add pkg to the list of this recipe's dependencies "
        self.log.log(1, "Added dependency: {}".format(pkg))
        self.deps.append(pkg)

    def source_add(self, src):
        " Add source URI "
        self.log.log(1, "Adding source: {0}".format(src))
        self.srcs.append(src)

    def configure_set_static(self, static_cfg_opts):
        " Add static config options "
        if self.static:
            self.log.log(1, "Adding static config options: {0}".format(static_cfg_opts))
            self.src_configure = static_cfg_opts

    def configure_set(self, cfg_opts):
        " Add config options "
        if not self.static or self.src_configure == "":
            self.log.log(1, "Adding config options: {0}".format(cfg_opts))
            self.src_configure = cfg_opts

    def install_set_static(self, arg):
        " Add static install options "
        if self.static:
            self.log.log(1, "Adding static install options: {0}".format(arg))
            self.src_install = arg

    def install_set(self, arg):
        " Add install options "
        if not self.static or self.src_install == "":
            self.log.log(1, "Adding install options: {0}".format(arg))
            self.src_install = arg

    def satisfy_begin(self, pkg_type):
        " Call this when finding a satisfy_*: line "
        match_obj = re.match(r'satisfy_([a-z]+):', pkg_type)
        self.curr_pkg_type = str(match_obj.group(1))
        self.log.log(1, "Found package list for package type {0}".format(self.curr_pkg_type))
        self.begin("distro_pkg_expr")

    def pl_pkg(self, pkg_name):
        " Called in a package requirements list, when a package name is found "
        self.log.log(1, "Adding package with name {}".format(pkg_name))
        new_pkg = PBPackageRequirement(pkg_name)
        if self.currpkg is not None:
            self.currpkg.second = new_pkg
        else:
            self.currpkg = new_pkg

    def pl_par(self, par):
        " Called in a package requirements list, when parens are found "
        if par == "(":
            self.pkgstack.append(self.currpkg)
            self.currpkg = None
        elif par == ")":
            prev = self.pkgstack.pop()
            if prev is not None:
                prev.second = self.currpkg
                self.currpkg = prev
        else:
            raise PBException("Error parsing recipe file {}. Invalid parens or something. Weird.".format(self.filename))

    def pl_cmp(self, cmpr):
        " Called in a package requirements list, when version comparator is found "
        self.log.log(1, "Adding version comparator {}".format(cmpr))
        if isinstance(self.currpkg, PBPackageRequirement):
            self.currpkg.compare = cmpr
        else:
            self.currpkg.second.compare = cmpr

    def pl_ver(self, ver):
        " Called in a package requirements list, when version number is found "
        self.log.log(1, "Adding version number {}".format(ver))
        if isinstance(self.currpkg, PBPackageRequirement):
            self.currpkg.version = ver
        else:
            self.currpkg.second.version = ver

    def pl_cmb(self, cmb):
        " Called in a package requirements list, when a logical combiner (||, &&) is found "
        self.log.log(1, "Found package combiner {}".format(cmb))
        if self.currpkg is None:
            raise PBException("Error parsing recipe file {}. Did not expect combiner here.".format(self.filename))
        self.currpkg = PBPackageRequirementPair(self.currpkg)
        self.currpkg.combiner = cmb

    def end_distro_pkg_expr(self, e):
        " Called when a list of package reqs is finished "
        self.log.log(1, "End of requirements list for package type {}".format(self.curr_pkg_type))
        self.satisfy[self.curr_pkg_type] = self.currpkg
        self.pkgstack = []
        self.currpkg = None
        self.begin("")

    def inherit(self, template):
        """ Inherit from a given template """
        try:
            filename = recipe_manager.recipe_manager.get_template_filename(template)
            print filename
        except PBException as e:
            self.log.warn("Recipe attempting to inherit from unknown template {}".format(template))
            return
        self.log.log(1, "Calling subscanner for file {}".format(filename))
        subscanner = Recipe(filename, lvars=self.lvars, static=self.static)
        # Get inherited values
        empty = [v for v in vars(self) if (getattr(self, v) is None or getattr(self, v) == "")]
        for v in empty:
            setattr(self, v, getattr(subscanner, v))
        # Copy the lvars over
        self.lvars = subscanner.lvars
        self.log.log(1, "Updated lvars: {}".format(self.lvars))

    def variable_begin(self, a):
        " Beginning of a variable line "
        match_obj = re.match(r'var\s+([\w\d_]+)\s+(=\!?)\s+"', a)
        self.varname = str(match_obj.group(1))
        if match_obj.group(2) == "=":
            self.varoverride = False
        else:
            self.varoverride = True
        self.log.log(1, "Found variable, name == {}, overriding: {}".format(self.varname, self.varoverride))
        if not self.lvars.has_key(self.varname) or self.varoverride:
            self.lvars[self.varname] = ""
            self.varoverride = True
        self.begin("variable")

    def variable_set(self, arg):
        " After variable_begin(), variable value is set here "
        if not self.lvars.has_key(self.varname) or self.varoverride:
            self.log.log(1, "Setting variable {} == {}".format(self.varname, arg))
            #self.lvars[self.varname] = self.var_replace(b)
            self.lvars[self.varname] = arg
        else:
            self.log.log(1, "Ignoring variable {} == {}".format(self.varname, arg))

    ### Plex: Patterns
    letter   = Range("AZaz")
    digit    = Range("09")
    gitbranchtype = Rep(letter | digit | Any("_-./"))
    revtype  = Rep(letter | digit | Any("_-."))
    name     = letter + Rep(letter | digit | Any("-"))
    var_name = letter + Rep(letter | digit | Any("_"))
    pkgname  = letter + Rep(letter | digit | Any("-.+_"))
    uri      = letter + Rep(letter | digit | Any("+@$-._:/"))
    number   = Rep1(digit)
    space    = Any(" \t\n")
    rspace   = Rep(space)
    comment  = Str("{") + Rep(AnyBut("}")) + Str("}")
    sep      = Any(", :/")
    eol      = Str("\r\n")|Str("\n")|Eof
    lpar     = Str("(")
    rpar     = Str(")")
    parens   = lpar | rpar
    comparators = Str(">=") | Str("<=") | Str("==") | Str("!=")
    assignments = Str("=") | Str("=!")
    combiner = Str("and") | Str("or") | Str('&&') | Str('||')
    version  = Rep(digit) + Rep(Str(".") + Rep(digit))

    ### Plex: Lexicon
    # Builds the lexical analyser
    lexicon = Lexicon([
        # Token Definitions. Format is: (pattern, action)
        # Begin(statename) is an action that puts the parser into
        # the state 'statename'.
        (Str("category:"), Begin("cat")),
        (Str("depends:"), Begin("deplist")),
        (Str("inherit:"), Begin("inherit")),
        (Str("configuredir:"), Begin("configuredir")),
        (Str("makedir:"), Begin("makedir")),
        (Str("installdir:"), Begin("installdir")),
        (Str("gitbranch:"), Begin("gitbranch")),
        (Str("gitargs:"), Begin("gitargs")),
        (Str("svnrev:"), Begin("svnrev")),
        (Str("gitrev:"), Begin("gitrev")),
        #(Str("satisfy_") + Rep1(letter) + Str(':'), Begin("distro_pkg_expr")),
        (Str("satisfy_") + Rep1(letter) + Str(':'), satisfy_begin),
        (Str("source:"), Begin("source_uri")),
        (Str("install_like:"), Begin("install_like")),
        (Str("configure") + Rep(space) + Str("{"), Begin("configure")),
        (Str("configure_static") + Rep(space) + Str("{"), Begin("configure_static")),
        (Str("make") + Rep(space) + Str("{"), Begin("make")),
        (Str("install") + Rep(space) + Str("{"), Begin("install")),
        (Str("install_static") + Rep(space) + Str("{"), Begin("install_static")),
        (Str("verify") + Rep(space) + Str("{"), Begin("verify")),
        (Str("uninstall") + Rep(space) + Str("{"), Begin("uninstall")),
        (Str("var") + Rep(space) + var_name + Rep(space) + assignments + Rep(space) + Str("\""), variable_begin),
        (name, TEXT),
        (number, 'int'),
        (space, IGNORE),
        (Str("#"), Begin('comment')),
        # State definitions: In every state, only certain tokens are accepted.
        # Tokens are of format (pattern, action). action can be a method of
        # this class.
        State('deplist', [
            (sep, IGNORE), (pkgname, deplist_add), (eol, mainstate),
        ]),
        State('distro_pkg_expr', [
            (sep, IGNORE),
            (pkgname, pl_pkg),
            (version, pl_ver),
            (parens, pl_par),
            (comparators, pl_cmp),
            (combiner, pl_cmb),
            (Eol, end_distro_pkg_expr),
        ]),
        State('source_uri', [
            (sep, IGNORE), (uri, source_add), (eol, mainstate),
        ]),
        State('install_like', [
            (sep, IGNORE), (pkgname, lambda scanner, arg: scanner.set_attr(arg, "install_like")), (Str("\n"), mainstate),
        ]),
        State('cat', [
            (sep, IGNORE), (pkgname, lambda scanner, arg: scanner.set_attr(arg, "category")), (eol, mainstate),
        ]),
        State('inherit', [
            (sep, IGNORE), (pkgname, inherit), (eol, mainstate),
            ]),
        State('configuredir', [
            (sep, IGNORE), (uri, lambda scanner, arg: scanner.set_attr(arg, "configuredir")), (eol, mainstate),
        ]),
        State('variable', [
            (Rep(AnyBut("\"")), variable_set), (Str("\""), mainstate),
        ]),
        State('makedir', [
            (sep, IGNORE), (uri, lambda scanner, arg: scanner.set_attr(arg, "makedir")), (eol, mainstate),
        ]),
        State('gitbranch', [
            (sep, IGNORE), (gitbranchtype, lambda scanner, arg: scanner.set_attr(arg, "git_branch")), (eol, mainstate),
        ]),
        State('gitargs', [
            (sep, IGNORE), (gitbranchtype, lambda scanner, arg: scanner.set_attr(arg, "git_args")), (eol, mainstate),
        ]),
        State('gitrev', [
            (sep, IGNORE), (revtype, lambda scanner, arg: scanner.set_attr(arg, "git_rev")), (eol, mainstate),
        ]),
        State('svnrev', [
            (sep, IGNORE), (revtype, lambda scanner, arg: scanner.set_attr(arg, "svn_rev")), (eol, mainstate),
        ]),
        State('installdir', [
            (sep, IGNORE), (uri, lambda scanner, arg: scanner.set_attr(arg, "install_dir")), (eol, mainstate),
        ]),
        State('configure_static', [
            (Rep(AnyBut("}")), configure_set_static), (Str("}"), mainstate),
        ]),
        State('configure', [
            (Rep(AnyBut("}")), configure_set), (Str("}"), mainstate),
        ]),
        State('make', [
            (Rep(AnyBut("}")), lambda scanner, arg: scanner.set_attr(arg, "src_make")), (Str("}"), mainstate),
        ]),
        State('install_static', [
            (Rep(AnyBut("}")), install_set_static), (Str("}"), mainstate),
        ]),
        State('install', [
            (Rep(AnyBut("}")), install_set), (Str("}"), mainstate),
        ]),
        State('verify', [
            (Rep(AnyBut("}")), lambda scanner, arg: scanner.set_attr(arg, "src_verify")), (Str("}"), mainstate),
        ]),
        State('uninstall', [
            (Rep(AnyBut("}")), lambda scanner, arg: scanner.set_attr(arg, "src_uninstall")), (Str("}"), mainstate),
        ]),
        State('comment', [
            (eol, Begin('')),
            (AnyChar, IGNORE)
        ])
    ]) # End Lexicon()


def get_recipe(pkgname):
    """
    Return a recipe object by its package name.
    """
    return Recipe(recipe_manager.recipe_manager.get_recipe_filename(pkgname))


if __name__ == "__main__":
    #recipe_filename = '/home/mbr0wn/src/pybombs/recipes/gr-specest.lwr'
    #recipe_filename = '/home/mbr0wn/src/pybombs/recipes/python.lwr'
    recipe_filename = '/home/mbr0wn/src/pybombs/recipes/gnuradio.lwr'
    pb_logging.logger.setLevel(1)
    scanner = Recipe(recipe_filename)
    for k, v in scanner.satisfy.iteritems():
        print "{}:".format(k)
        print str(v)
    print scanner.lvars
