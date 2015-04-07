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
from plex import *
import pb_logging

debug_en = True

class Recipe(Scanner):
    """
    Represents a recipe. Internally, it's a lexical scanner for the actual
    recipe.
    """
    def __init__(self, filename, lvars=None):
        self.log = pb_logging.logger
        self.deps = []
        self.srcs = []


        if(not lvars):
            #lvars = vars_copy(vars)
            lvars = []
        self.lvars = lvars
        if debug_en:
            print "init scanner with lvars = %s"%(lvars)
        #self.recipe = recipe
        #self.recipe.scanner = self

        if not os.path.exists(filename):
            print "Missing file %s"%(filename)
            raise RuntimeError
        f = open(filename,"r")
        Scanner.__init__(self, self.lexicon, f, filename)
        self.begin("")
#        print dir(self)
#        print self.cur_line
        if debug_en:
            print "Parsing "+filename
        while 1:
            token = Scanner.read(self)
#            print token
            if token[0] is None:
                break
        f.close()


    def var_replace(self, s):
        #for k in vars.keys():
        #    s = s.replace("$%s"%(k), vars[k])
        #for k in self.lvars.keys():
            #s = s.replace("$%s"%(k), self.lvars[k])
        #for k in self.lvars.keys():
            #s = s.replace("$%s"%(k), self.lvars[k])
        #for k in vars.keys():
            #s = s.replace("$%s"%(k), vars[k])
        #return s
        pass

    def fancy_var_replace(self,s,d):
        finished = False
        while not finished:
            os = s
            for k in d.keys():
                s = s.replace("$%s"%(k), d[k])
            #v.print_v(v.PDEBUG, (s,os))
            if(os == s):
                finished = True
        return s

    def replc(self, m):
#        print "GOT REPL C: %s"%(str([m.group(1), m.group(2), m.group(3)]))
        #if m.group(1) == self.tmpcond:
            #return  m.group(2)
        #else:
            #return  m.group(3)
        pass

    def var_replace_all(self, s):
        finished = False
        #lvars = vars_copy(self.lvars)
        #lvars = []
        #lvars.update(vars)
        #s = self.fancy_var_replace(s, lvars)
        #for k in lvars:
            #fm = "\{([^\}]*)\}"
            #rg = r"%s==(\w+)\?%s:%s"%(k,fm,fm)
            #self.tmpcond = lvars[k]
            #s = re.sub(rg, self.replc, s)
        return s

    def config_filter(self, in_string):
        #prefix = re.compile("-DCMAKE_INSTALL_PREFIX=\S*")
        #toolchain = re.compile("-DCMAKE_TOOLCHAIN_FILE=\S*")
        #cmake = re.compile("cmake \S* ")
        #CC = re.compile("CC=\S* ")
        #CXX = re.compile("CXX=\S* ")
        #if str(os.environ.get('PYBOMBS_SDK')) == 'True':
            #cmk_cmd_match = re.search(cmake, in_string)
            #if cmk_cmd_match:
                #idx = in_string.find(cmk_cmd_match.group(0)) + len(cmk_cmd_match.group(0))
                #in_string = re.sub(prefix, "-DCMAKE_INSTALL_PREFIX=" + config.get('config', 'sdk_prefix'), in_string)
                #if re.search(toolchain, in_string):
                    #in_string = re.sub(toolchain, "-DCMAKE_TOOLCHAIN_FILE=" + config.get('config', 'toolchain'), in_string)
                #else:
                    #in_string = in_string[:idx] +  "-DCMAKE_TOOLCHAIN_FILE=" + config.get('config', 'toolchain') + ' ' + in_string[idx:]
                #if re.search(CC, in_string):
                    #in_string = re.sub(CC, "", in_string)
                #if re.search(CXX, in_string):
                    #in_string = re.sub(CXX, "", in_string)
        print in_string
        return in_string

    def installed_filter(self, in_string):
        #installed = re.compile("make install")
        #if str(os.environ.get('PYBOMBS_SDK')) == 'True':
            #print in_string
            #mk_inst_match = re.search(installed, in_string)
            #if mk_inst_match:
                #idx = in_string.find(mk_inst_match.group(0)) + len(mk_inst_match.group(0))
                #in_string = in_string[:idx] +  " DESTDIR=" + config.get('config', 'sandbox') + ' ' + in_string[idx:]
        print in_string
        return in_string

    def deplist_add(self, pkg):
        " Add pkg to the list of this recipe's dependencies "
        self.deps.append(pkg)


    def source_add(self, src):
        self.log.log(0, "Adding source: {0}".format(src))
        self.srcs.append(src)

    def pl_pkg(self, e):
        #npkg = pkgreq(e)
        #if(self.recipe.currpkg):
            #self.recipe.currpkg.second = npkg
        #else:
            #self.recipe.currpkg = npkg
        pass

    def pl_par(self, e):
        pass
        #if(e == "("):
            #self.recipe.pkgstack.append(self.recipe.currpkg)
            #self.recipe.currpkg = None
        #elif(e == ")"):
            #prev = self.recipe.pkgstack.pop()
            #if(not (prev == None)):
                #prev.second = self.recipe.currpkg
                #self.recipe.currpkg = prev
            #else:
                #self.recipe.currpkg = self.recipe.currpkg
        #else:
            #sys.exit(-1)

    def pl_cmp(self, e):
        pass
        #if(self.recipe.currpkg.__class__.__name__ == "pkgreq"):
            #self.recipe.currpkg.compare = e
        #else:
            #self.recipe.currpkg.second.compare = e

    def pl_ver(self, e):
        pass
        #if(self.recipe.currpkg.__class__.__name__ == "pkgreq"):
            #self.recipe.currpkg.version = e
        #else:
            #self.recipe.currpkg.second.version = e

    def pl_cmb(self, e):
        pass
        #assert(self.recipe.currpkg)
        #self.recipe.currpkg = pr_pair(self.recipe.currpkg)
        #self.recipe.currpkg.combiner = e

    def distro_pkg_expr(self, pkg_expr):
        if debug_en:
            print "DEB satisfier EXPR ", e
            #print self.recipe.currpkg
        #self.recipe.satisfy_deb = self.recipe.currpkg
        #self.recipe.clearpkglist()
        self.begin("")

    def category_set(self,c):
        if debug_en:
            print "Setting category: "+c
        #self.recipe.category = c

    def mainstate(self,a):
        self.begin("")

    def configure_set_static(self,a):
        pass
        #if config.get("config","static") == "True":
            #self.recipe.scr_configure = a

    def configure_set(self,a):
        pass
        #if config.get("config","static") == "False":
            #self.recipe.scr_configure = a
        #else:
            #if self.recipe.scr_configure == "":
                #self.recipe.scr_configure = a

    def make_set(self,a):
        #self.recipe.scr_make = a
        pass

    def install_set_static(self,a):
        pass
        #if config.get("config","static") == "True":
            #self.recipe.scr_install = a

    def install_set(self,a):
        pass
        #if config.get("config","static") == "False":
            #self.recipe.scr_install = a
        #else:
            #if self.recipe.scr_install == "":
                #self.recipe.scr_install = a

    def verify_set(self,a):
        pass
        #self.recipe.scr_verify = a

    def uninstall_set(self,a):
        pass
        #self.recipe.scr_uninstall = a

    def install_like_set(self,a):
        pass
        #self.recipe.install_like = a

    def configuredir(self,a):
        if debug_en:
            print "configuredir: %s"%(a)
        #self.recipe.configuredir = a

    def makedir(self,a):
        if debug_en:
            print "makedir: %s"%(a)
        #self.recipe.makedir = a

    def gitbranch(self,a):
        if debug_en:
            print "gitbranch: %s"%(a)
        #self.recipe.git_branch = a

    def gitargs(self,a):
        if debug_en:
            print "gitargs: %s"%(a)
            print "gitbranch: %s"%(a)
        #self.recipe.git_args = a

    def gitrev(self,a):
        if debug_en:
            print "gitrev: %s"%(a)
        #self.recipe.gitrev = a

    def svnrev(self,a):
        if debug_en:
            print "svnrev: %s"%(a)
        #self.recipe.svnrev = a

    def installdir(self,a):
        if debug_en:
            print "installdir: %s"%(a)
        #self.recipe.installdir = self.installdir_filter(a)

    def installdir_filter(self, a):
        if str(os.environ.get('PYBOMBS_SDK')) == 'True':
            return a + '_sdk'
        else:
            return a

    def inherit(self,a):
        pass
        #subscanner = recipescanner(topdir + "/templates/"+a+".lwt", self.recipe, self.lvars)
        #self.lvars = subscanner.lvars
            #die( "attempted to inherit from %s but did not exist"%(a) )

    def variable_begin(self,a):
        #print "var_begin"
        #print a
        m = re.match(r'var\s+([\w\d_]+)\s+(=\!?)\s+"', a)
        self.varname = str(m.group(1))
        if(m.group(2) == "="):
            self.varoverride = False
        else:
            self.varoverride = True
        #print "var = %s "%(self.varname)
        #print "lvars = %s"%(self.lvars)
        #if (not self.lvars.has_key(self.varname)) or (self.varoverride):
            #self.lvars[self.varname] = "";
            #self.varoverride = True
        self.begin("variable")

    def variable_set(self,b):
        #if (not self.lvars.has_key(self.varname)) or (self.varoverride):
            #if debug_en:
                #print "var_set(%s) = %s"%(self.varname,b)
            #self.lvars[self.varname] = self.var_replace(b)
        #else:
            #if debug_en:
                #print "(ignored) var_set(%s) = %s"%(self.varname,b)
        pass


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
        (Str("satisfy_") + Rep1(letter) + Str(':'), Begin("distro_pkg_expr")),
        (Str("source:"), Begin("source_uri")),
        (Str("install_like:"), Begin("install_like")),
        (Str("configure") + Rep(space) + Str("{"), Begin("configure")),
        (Str("configure_static") + Rep(space) + Str("{"), Begin("configure_static")),
        (Str("make") + Rep(space) + Str("{"), Begin("make")),
        (Str("install") + Rep(space) + Str("{"), Begin("install")),
        (Str("install_static") + Rep(space) + Str("{"), Begin("install_static")),
        (Str("verify") + Rep(space) + Str("{"), Begin("verify")),
        (Str("uninstall") + Rep(space) + Str("{"), Begin("uninstall")),
        (Str("var") + Rep(space) + var_name + Rep(space) + assignments + Rep(space) + Str("\"") , variable_begin ),
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
            (version,pl_ver),
            (parens,pl_par),
            (comparators, pl_cmp),
            (combiner, pl_cmb),
            (Eol, distro_pkg_expr),
            ]),
        State('source_uri', [
            (sep, IGNORE), (uri, source_add), (eol, mainstate),
            ]),
        State('install_like', [
            (sep, IGNORE), (pkgname, install_like_set), (Str("\n"), mainstate),
            ]),
        State('cat', [
            (sep, IGNORE), (pkgname, category_set), (eol, mainstate),
            ]),
        State('inherit', [
            (sep, IGNORE), (pkgname, inherit), (eol, mainstate),
            ]),
        State('inherit', [
            (sep, IGNORE), (pkgname, inherit), (eol, mainstate),
            ]),
        State('configuredir', [
            (sep, IGNORE), (uri, configuredir), (eol, mainstate),
            ]),
        State('variable', [
            (Rep(AnyBut("\"")), variable_set), (Str("\""), mainstate),
            ]),
        State('makedir', [
            (sep, IGNORE), (uri, makedir), (eol, mainstate),
            ]),
        State('gitbranch', [
            (sep, IGNORE), (gitbranchtype, gitbranch), (eol, mainstate),
            ]),
        State('gitargs', [
            (sep, IGNORE), (gitbranchtype, gitargs), (eol, mainstate),
            ]),
        State('gitrev', [
            (sep, IGNORE), (revtype, gitrev), (eol, mainstate),
            ]),
        State('svnrev', [
            (sep, IGNORE), (revtype, svnrev), (eol, mainstate),
            ]),
        State('installdir', [
            (sep, IGNORE), (uri, installdir), (eol, mainstate),
            ]),
        State('configure_static', [
            (Rep(AnyBut("}")), configure_set_static), (Str("}"), mainstate),
            ]),
        State('configure', [
            (Rep(AnyBut("}")), configure_set), (Str("}"), mainstate),
            ]),
        State('make', [
            (Rep(AnyBut("}")), make_set), (Str("}"), mainstate),
            ]),
        State('install_static', [
            (Rep(AnyBut("}")), install_set_static), (Str("}"), mainstate),
            ]),
        State('install', [
            (Rep(AnyBut("}")), install_set), (Str("}"), mainstate),
            ]),
        State('verify', [
            (Rep(AnyBut("}")), verify_set), (Str("}"), mainstate),
            ]),
        State('uninstall', [
            (Rep(AnyBut("}")), uninstall_set), (Str("}"), mainstate),
            ]),
        State('comment', [
            (eol, Begin('')),
            (AnyChar, IGNORE)
            ])
        ]) # End Lexicon()


if __name__ == "__main__":
    recipe_filename = '../recipes/gr-specest.lwr'
    pb_logging.logger.setLevel(0)
    scanner = Recipe(recipe_filename)

