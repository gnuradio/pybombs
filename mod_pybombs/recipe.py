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

from globals import *;
from plex import *;
from sysutils import *;
import fetch
from update import update;

import pybombs_ops;
import logging,sys

logger = logging.getLogger('PyBombs.recipe')

debug_en = False;

# structure for a dependency package (name, comparator, version) (for rpm or deb)
class pkgreq:
    def __init__(self, name):
        self.name = name;
        self.compare = None;
        self.version = None;
    def ev(self, func):
        return func(self.name, self.compare, self.version);
    def __str__(self,lvl=0):
        return " "*lvl + "pkgreq(%s,%s,%s)"%(self.name, self.compare, self.version);

# joining logic for multiple dep packages (for rpms and debs)   
class pr_pair:
    def __init__(self, pkg):
        if debug_en:
            print "pr_pair(%s,...)"%(pkg)
        self.first = pkg;
        self.second = None;
        self.combiner = None;
    def ev(self,func):
        #print self;
        if(self.combiner == "&&"):
            return self.first.ev(func) and self.second.ev(func);
        elif(self.combiner == "||"):
            return self.first.ev(func) or self.second.ev(func);
    def __str__(self, lvl=0):
        a = " "*lvl + "pr_pair: (%s)"%(self.combiner) + "\n"
        a = a + " "*lvl + self.first.__str__(1) + "\n"
        if(self.second):
            a = a + " "*lvl + self.second.__str__(1);
        else:
            a = a + " "*lvl + "None"
        return a;

class recipescanner(Scanner):

    def var_replace(self,s):
        #for k in vars.keys():
        #    s = s.replace("$%s"%(k), vars[k]);
        for k in self.lvars.keys():
            s = s.replace("$%s"%(k), self.lvars[k]);
        for k in self.lvars.keys():
            s = s.replace("$%s"%(k), self.lvars[k]);
        for k in vars.keys():
            s = s.replace("$%s"%(k), vars[k]);
        return s;

    def fancy_var_replace(self,s,d):
        finished = False
        while not finished:
            os = s;
            for k in d.keys():
                s = s.replace("$%s"%(k), d[k]);
            print (s,os)
            if(os == s):
                finished = True;
        return s;
    
    def replc(self, m):
#        print "GOT REPL C: %s"%(str([m.group(1), m.group(2), m.group(3)]))
        if m.group(1) == self.tmpcond:
            return  m.group(2);
        else:
            return  m.group(3);

    def var_replace_all(self, s):
        finished = False
        lvars = vars_copy(self.lvars);
        lvars.update(vars);
        s = self.fancy_var_replace(s, lvars);
        for k in lvars:
            fm = "\{([^\}]*)\}"
            rg = r"%s==(\w+)\?%s:%s"%(k,fm,fm);
            self.tmpcond = lvars[k];
            s = re.sub(rg, self.replc, s);
        return s;

    def deplist_add(self,a):
        self.recipe.depends.append(a);

        # load recipes of dependencies first now
        if not global_recipes.has_key(a):
            global_recipes[a] = recipe(a);

        
    def source_add(self,a):
        if debug_en:
            print "Adding source: " + a;
        self.recipe.source.append(self.var_replace(a));

        # make sure we depend on git or svn if used to retrieve
        try:
            if(str(a[0:6]) == "git://"):
                self.recipe.depends.append("git");
            if(str(a[0:6]) == "svn://"):
                self.recipe.depends.append("subversion");
        except:
            pass

    def pl_pkg(self, e):    
        npkg = pkgreq(e);
        if(self.recipe.currpkg):
            self.recipe.currpkg.second = npkg;
        else:
            self.recipe.currpkg = npkg;

    def pl_par(self, e):
        if(e == "("):
            self.recipe.pkgstack.append(self.recipe.currpkg);
            self.recipe.currpkg = None;
        elif(e == ")"):
            prev = self.recipe.pkgstack.pop();
            if(not (prev == None)):
                prev.second = self.recipe.currpkg;
                self.recipe.currpkg = prev;
            else:
                self.recipe.currpkg = self.recipe.currpkg;
        else:
            sys.exit(-1);

    def pl_cmp(self, e):
        if(self.recipe.currpkg.__class__.__name__ == "pkgreq"):
            self.recipe.currpkg.compare = e;
        else:
            self.recipe.currpkg.second.compare = e;
    
    def pl_ver(self, e):
        if(self.recipe.currpkg.__class__.__name__ == "pkgreq"):
            self.recipe.currpkg.version = e;
        else:
            self.recipe.currpkg.second.version = e;

    def pl_cmb(self, e):
        assert(self.recipe.currpkg);
        self.recipe.currpkg = pr_pair(self.recipe.currpkg);
        self.recipe.currpkg.combiner = e;

    def debexpr(self,e):
        if debug_en:
            print "DEB satisfier EXPR"
            print self.recipe.currpkg;
        self.recipe.satisfy_deb = self.recipe.currpkg;
        self.recipe.clearpkglist();
        self.begin("")

    def rpmexpr(self,e):
        if debug_en:
            print "RPM satisfier EXPR"
            print self.recipe.currpkg;
        self.recipe.satisfy_rpm = self.recipe.currpkg;
        self.recipe.clearpkglist();
        self.begin("")

    def category_set(self,c):
        if debug_en:
            print "Setting category: "+c;
        self.recipe.category = c;

    def mainstate(self,a):
        self.begin("")

    def configure_set(self,a):
        self.recipe.scr_configure = a;

    def make_set(self,a):
        self.recipe.scr_make = a;

    def install_set(self,a):
        self.recipe.scr_install = a;
    
    def uninstall_set(self,a):
        self.recipe.scr_uninstall = a;
        
    def install_like_set(self,a):
        self.recipe.install_like = a

    def configuredir(self,a):
        if debug_en:
            print "configuredir: %s"%(a);
        self.recipe.configuredir = a;
    
    def makedir(self,a):
        if debug_en:
            print "makedir: %s"%(a);
        self.recipe.makedir = a;

    def gitbranch(self,a):
        if debug_en:
            print "gitbranch: %s"%(a);
        self.recipe.gitbranch = a;
    
    def gitrev(self,a):
        if debug_en:
            print "gitrev: %s"%(a);
        self.recipe.gitrev = a;

    def svnrev(self,a):
        if debug_en:
            print "svnrev: %s"%(a);
        self.recipe.svnrev = a;

    def makedir(self,a):
        if debug_en:
            print "makedir: %s"%(a);
        self.recipe.makedir = a;

    def installdir(self,a):
        if debug_en:
            print "installdir: %s"%(a);
        self.recipe.installdir = a;

    def inherit(self,a):
        subscanner = recipescanner(topdir + "/templates/"+a+".lwt", self.recipe, self.lvars);
        self.lvars = subscanner.lvars;
            #die( "attempted to inherit from %s but did not exist"%(a) );

    def variable_begin(self,a):
        #print "var_begin"
        #print a;
        m = re.match(r'var\s+([\w\d_]+)\s+(=\!?)\s+"', a);
        self.varname = str(m.group(1));
        if(m.group(2) == "="):
            self.varoverride = False;
        else:
            self.varoverride = True;
        #print "var = %s "%(self.varname);
        #print "lvars = %s"%(self.lvars);
        if (not self.lvars.has_key(self.varname)) or (self.varoverride):
            self.lvars[self.varname] = ""; 
            self.varoverride = True;
        self.begin("variable");

    def variable_set(self,b):
        if (not self.lvars.has_key(self.varname)) or (self.varoverride):
            if debug_en:
                print "var_set(%s) = %s"%(self.varname,b);
            self.lvars[self.varname] = self.var_replace(b);
        else:
            if debug_en:
                print "(ignored) var_set(%s) = %s"%(self.varname,b);

    letter = Range("AZaz")
    digit = Range("09")
    revtype = Rep(letter | digit | Any("_-."))
    name = letter + Rep(letter | digit | Any("-"))
    var_name = letter + Rep(letter | digit | Any("_"));
    pkgname = letter + Rep(letter | digit | Any("-.+_"))
    uri = letter + Rep(letter | digit | Any("+@$-._:/"))
    number = Rep1(digit)
    space = Any(" \t\n")
    rspace = Rep(space)
    comment = Str("{") + Rep(AnyBut("}")) + Str("}")
    sep = Any(", :/");
    eol = Str("\r\n")|Str("\n")|Eof

    lpar = Str("(");
    rpar = Str(")");
    parens = lpar | rpar;
    comparators = Str(">=") | Str("<=") | Str("==") | Str("!=")
    assignments = Str("=") | Str("=!")
    combiner = Str("and") | Str("or") | Str('&&') | Str('||');
    version = Rep(digit) + Rep(Str(".") + Rep(digit))

    lexicon = Lexicon([
        (Str("category:"), Begin("cat")),
        (Str("depends:"), Begin("deplist")),
        (Str("inherit:"), Begin("inherit")),
        (Str("configuredir:"), Begin("configuredir")),
        (Str("makedir:"), Begin("makedir")),
        (Str("installdir:"), Begin("installdir")),
        (Str("gitbranch:"), Begin("gitbranch")),
        (Str("svnrev:"), Begin("svnrev")),
        (Str("gitrev:"), Begin("gitrev")),
        (Str("satisfy_deb:"), Begin("debexpr")),
        (Str("satisfy_rpm:"), Begin("rpmsat")),
        (Str("source:"), Begin("source_uri")),
        (Str("install_like:"), Begin("install_like")),
        (Str("configure") + Rep(space) + Str("{"), Begin("configure")),
        (Str("make") + Rep(space) + Str("{"), Begin("make")),
        (Str("install") + Rep(space) + Str("{"), Begin("install")),
        (Str("uninstall") + Rep(space) + Str("{"), Begin("uninstall")),
        (Str("var") + Rep(space) + var_name + Rep(space) + assignments + Rep(space) + Str("\"") , variable_begin ),
        (name, TEXT),
        (number, 'int'),
        (space,     IGNORE),
        (Str("#"), Begin('comment')),
        State('deplist', [
            (sep, IGNORE), (pkgname, deplist_add), (eol, mainstate),
            ]),
        State('debexpr', [
            (sep, IGNORE), (pkgname, pl_pkg), (version,pl_ver), (parens,pl_par), (comparators, pl_cmp), (combiner, pl_cmb), (Eol, debexpr), 
            ]),
        State('rpmsat', [
            (sep, IGNORE), (pkgname, pl_pkg), (version,pl_ver), (parens,pl_par), (comparators, pl_cmp), (combiner, pl_cmb), (Eol, rpmexpr), 
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
            (sep, IGNORE), (revtype, gitbranch), (eol, mainstate),
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
        State('configure', [
            (Rep(AnyBut("}")), configure_set), (Str("}"), mainstate),
            ]),
        State('make', [
            (Rep(AnyBut("}")), make_set), (Str("}"), mainstate),
            ]),
        State('install', [
            (Rep(AnyBut("}")), install_set), (Str("}"), mainstate),
            ]),
        State('uninstall', [
            (Rep(AnyBut("}")), uninstall_set), (Str("}"), mainstate),
            ]),
        State('comment', [
            (eol, Begin('')),
            (AnyChar, IGNORE)
            #(AnyChar, IGNORE)
            ])

        ])


    def __init__(self, filename, recipe, lvars = None):

        if(not lvars):
            lvars = vars_copy(vars);
        self.lvars = lvars;
        if debug_en:
            print "init scanner with lvars = %s"%(lvars)
        self.recipe = recipe;
        self.recipe.scanner = self

        if not os.path.exists(filename):
            print "Missing file %s"%(filename)
            raise RuntimeError

        f = open(filename,"r");
        Scanner.__init__(self, self.lexicon, f, filename);
        self.begin("");
#        print dir(self);
#        print self.cur_line

        if debug_en:
            print "Parsing "+filename       
        while 1:
            token = Scanner.read(self);
#            print token;
            if token[0] is None:
                break;
        
        f.close();


class recipe:


    def __init__(self, name):
        self.name = name;
        self.clearpkglist();
        self.depends = [];
        self.satisfy_deb = None;
        self.satisfy_rpm = None;
        self.source = [];
        self.install_like = None
        self.category = None;
        self.satisfier = None;
        self.scr_configure = "";
        self.scr_make = "";
        self.scr_install = "";
        self.scr_uninstall = "";
        self.configuredir = "";
        self.makedir = "";
        self.installdir = "";
        self.gitbranch = "master";
        self.svnrev = "HEAD";
        self.gitrev = "";
        if name != 'all':        
            self.scan = recipescanner("recipes/%s.lwr"%(name), self);
        self.install_order = [ ("fetch",self.fetch), ("configure",self.configure), ("make",self.make), ("installed",self.installed) ];

    # empty out working variables for the parser/scanner
    # while parsing a pkg logic expression
    def clearpkglist(self):
        self.pkgstack = [];
        self.currpkg = None;
        
    def newest_version(self):
        if(self.satisfy()):
            ud = update(self);
            return ud.check();
        else:
            # pretend we are up to date if not installed
            return True;

    # return a list of packages which depend on this one
    def get_dependents(self):
        #print "%s.get_dependents()"%(self.name);
        d = [];
        for r in global_recipes:
#            print r;
            rp = global_recipes[r];
            if(self.name in rp.depends):
                d.append(r);
                d.extend(rp.get_dependents());
        return list(set(d));

    def satisfy(self):

        # early out if we have already checked this
        if(vars.has_key("%s.satisfier"%(self.name))):
            self.satisfied = vars["%s.satisfier"%(self.name)];
            return True;

        if(any(self.name in s for s in force_list)):
            self.satisfier = "force";
            vars["%s.satisfier"%(self.name)] = self.satisfier;
            return True;
    
        if(inv.has(self.name)):
            if(inv.state(self.name) == "installed"):
                self.satisfier = "inventory";
                vars["%s.satisfier"%(self.name)] = self.satisfier;
                return True;                                                    
               
        if(have_debs(self.satisfy_deb)):
            self.satisfier = "deb";
            vars["%s.satisfier"%(self.name)] = self.satisfier;
            return True;

        if(have_rpms(self.satisfy_rpm)):
            self.satisfier = "rpm";
            vars["%s.satisfier"%(self.name)] = self.satisfier;
            return True;
        
        return False;

    def recursive_satisfy(self, recurse_if_installed=False):
        ll = [];
        print "%s dep [%s]"%(self.name, self.depends)
 
        selfsat = self.satisfy();

        # first make sure children are satisfied
        if(recurse_if_installed or not selfsat):
            for i in self.depends:
                try:
                    ll.extend(global_recipes[i].recursive_satisfy());
                except:
                    die("broken package dependency %s -> %s (%s recipe not found)"%(self.name, i, i));

        # then satisfy self
        if(not selfsat):
            ll.append(self.name);

        return ll;

    def install(self):
        print "install called (%s)"%(self.name)
        order =  vars["satisfy_order"];
        order = order.replace(" ","").lower();
        types = None;
        if order.find(',') > 0:            
            types = order.split(",");
        elif order.find('-') > 0:
            types = order.split("-") # needed for Jenkins bug https://issues.jenkins-ci.org/browse/JENKINS-12439
        else:
            types = order.split(","); # needed for single item case
        if vars.has_key("install_like"):
            copyFrom = vars["install_like"]
            types.remove(global_recipes[copyFrom].satisfier)
            types.insert(0, global_recipes[copyFrom].satisfier)
        if self.name == 'all':
            print "pseudo installation ok"
            return True;
        if(types==None):
            logging.error('\x1b[31m' + "Your satisfy order (%s) provides no way to satisfy the dependency (%s) - please consider changing your satisfy order to \"deb,src\" or \"deb,rpm\" in config.dat!!!"%(order,self.name)+ '\x1b[0m');
            sys.exit(-1);
        print "install type priority: " + str(types);
        
        for type in types:
            st = False;
            if(type == "src"):
                st = self.install_src();
            elif(type == "rpm"):
                st = self.install_rpm();
            elif(type == "deb"):
                st = self.install_deb();
            else:
                die( "unknown install type: %s"%(type) );
            if(st):
                print "installation ok via: %s"%(type);
                return True;
        die("failed to install %s"%(self.name));   
        return False;

    def install_rpm(self):
        print "install rpm called (%s)"%(self.name)
        # this is not possible if we do not have rpm satisfiers
        if((self.satisfy_rpm == None) or ((type(self.satisfy_rpm) == type([])) and (len(self.satisfy_rpm) == 0))):
            print "no rpm satisfiers available"
            return False;
        elif self.satisfy_rpm and not have_rpms(self.satisfy_rpm):
            print "rpm is not available locally"
            print "check remote repositories..."
            if not rpms_exist(self.satisfy_rpm):
                return False;
        print "CONDUCTING RPM INSTALL"
        return rpm_install(self.satisfy_rpm);  
    
    def install_deb(self):
        print "install deb called (%s)"%(self.name)
        # this is not possible if we do not have deb satisfiers
        if((self.satisfy_deb == None) or ((type(self.satisfy_deb) == type([])) and (len(self.satisfy_deb) == 0))):
            print "no deb satisfiers available"
            return False;
        elif self.satisfy_deb and not have_debs(self.satisfy_deb):
            print "deb is not available locally"
            print "check remote repositories..."
            if not debs_exist(self.satisfy_deb):
                return False;
        print "CONDUCTING DEB INSTALL"
        return deb_install(self.satisfy_deb);  

    def install_src(self):
        print "install src called (%s)"%(self.name)

        # basic source installation requirements
        # install gcc etc before proceeding to build steps
        req = ["gcc"];
        for p in req:
            try:
                if(not global_recipes[p].satisfy()):
                    global_recipes[p].install();
            except:
                return False;

        state = inv.state(self.name);
        print "state = %s"%(state)
        step = 0;
        for i in range( len( self.install_order ) ):
            if( self.install_order[i][0] == state ):
                step = i+1;

        # iterate through the install steps of current package
        while(step < len(self.install_order)):
            print "Current step: (%s :: %s)"%(self.name, self.install_order[step][0]);
            # run the installation step
            self.install_order[step][1]();
            # update value in inventory
            inv.set_state(self.name, self.install_order[step][0]);
            if(self.install_order[step][0] == "fetch"):
                # if we just fetched a package, store its version and source
                print "setting installed version info (%s,%s)"%(self.last_fetcher.used_source,self.last_fetcher.version)
                inv.set_prop(self.name, "source", self.last_fetcher.used_source);
                inv.set_prop(self.name, "version", self.last_fetcher.version);
            step = step + 1;

        return True;
     
    def fetched(self):
        fetcher = fetch.fetcher(self.source, self);
        return fetcher.fetched();
   
    def fetch(self):
        # this is not possible if we do not have sources
        if(len(self.source) == 0):
            print "WARNING: no sources available for package %s!"%(self.name)
            return True
        fetcher = fetch.fetcher(self.source, self);
        fetcher.fetch();
        if(not fetcher.success):
            if(len(self.source) == 0):
                raise Exception("Failed to Fetch package '%s' no sources were provided! '%s'!"%(self.name, self.source));
            else:
                raise Exception("Failed to Fetch package '%s' sources were '%s'!"%(self.name, self.source));

        # update value in inventory
        inv.set_state(self.name, "fetch");
        self.last_fetcher = fetcher;
        print "Setting fetched version info (%s,%s)"%(fetcher.used_source, fetcher.version)
        inv.set_prop(self.name, "source", fetcher.used_source);
        inv.set_prop(self.name, "version", fetcher.version);
        

    def check_stat(self, stat, step):
        if(stat == 0):
            return;
        logging.error('\x1b[31m' + "PyBOMBS %s step failed for package (%s) please see bash output above for a reason (hint: look for the word Error)"%(step, self.name) + '\x1b[0m');
        sys.exit(-1);

    def configure(self):
        print "configure"
        mkchdir(topdir + "/src/" + self.name + "/" + self.installdir)
        st = bashexec(self.scanner.var_replace_all(self.scr_configure));
        self.check_stat(st, "Configure");

    def make(self):
        print "make"
        mkchdir(topdir + "/src/" + self.name + "/" + self.installdir)
        st = bashexec(self.scanner.var_replace_all(self.scr_make));
        self.check_stat(st, "Make");

    def installed(self):
        # perform installation, file copy
        print "installed"
        mkchdir(topdir + "/src/" + self.name + "/" + self.installdir)
        st = bashexec(self.scanner.var_replace_all(self.scr_install));
        self.check_stat(st, "Install");

    # run package specific make uninstall
    def uninstall(self):
        try:
            if(self.satisfier == "inventory"):
                mkchdir(topdir + "/src/" + self.name + "/" + self.installdir)
                st = bashexec(self.scanner.var_replace_all(self.scr_uninstall));
                print "bash return val = %d"%(st);
                self.satisfier = None;
                del vars["%s.satisfier"%(self.name)]
            else:
                print "pkg not installed from source, ignoring"
        except:
            print "local build dir does not exist"   

    # clean the src dir
    def clean(self):
        os.chdir(topdir + "/src/");
        rmrf(self.name);
        inv.set_state(self.name,None);


