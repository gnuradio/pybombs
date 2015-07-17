#!/usr/bin/env python2
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
import output_proc
import verbosity as v

debug_en = False;

class PBRecipeException(Exception):
    """ Is thrown when a Pybombs recipe fails one of its steps """
    pass

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
            v.print_v(v.PDEBUG, (s,os))
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

    def config_filter(self, in_string):
        prefix = re.compile("-DCMAKE_INSTALL_PREFIX=\S*")
        toolchain = re.compile("-DCMAKE_TOOLCHAIN_FILE=\S*")
        cmake = re.compile("cmake \S* ")
        CC = re.compile("CC=\S* ")
        CXX = re.compile("CXX=\S* ")
        if str(os.environ.get('PYBOMBS_SDK')) == 'True':
            cmk_cmd_match = re.search(cmake, in_string)
            if cmk_cmd_match:
                idx = in_string.find(cmk_cmd_match.group(0)) + len(cmk_cmd_match.group(0))
                in_string = re.sub(prefix, "-DCMAKE_INSTALL_PREFIX=" + config.get('config', 'sdk_prefix'), in_string);
                if re.search(toolchain, in_string):
                    in_string = re.sub(toolchain, "-DCMAKE_TOOLCHAIN_FILE=" + config.get('config', 'toolchain'), in_string)
                else:
                    in_string = in_string[:idx] +  "-DCMAKE_TOOLCHAIN_FILE=" + config.get('config', 'toolchain') + ' ' + in_string[idx:]
                if re.search(CC, in_string):
                    in_string = re.sub(CC, "", in_string)
                if re.search(CXX, in_string):
                    in_string = re.sub(CXX, "", in_string)
                                       
            
        print in_string
        return in_string

    def installed_filter(self, in_string):
        installed = re.compile("make install")
        if str(os.environ.get('PYBOMBS_SDK')) == 'True':
            print in_string
            mk_inst_match = re.search(installed, in_string)
            if mk_inst_match:
                idx = in_string.find(mk_inst_match.group(0)) + len(mk_inst_match.group(0))
                in_string = in_string[:idx] +  " DESTDIR=" + config.get('config', 'sandbox') + ' ' + in_string[idx:]
                    
                    
                                       
            
        print in_string
        return in_string

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

    def description_set(self,d):
        if debug_en:
            print "Setting description: "+d;
        self.recipe.description = d;

    def mainstate(self,a):
        self.begin("")

    def configure_set_static(self,a):
        if config.get("config","static") == "True":
            self.recipe.scr_configure = a;

    def configure_set(self,a):
        if config.get("config","static") == "False":
            self.recipe.scr_configure = a;
        else:
            if self.recipe.scr_configure == "":
                self.recipe.scr_configure = a;

    def make_set(self,a):
        self.recipe.scr_make = a;

    def install_set_static(self,a):
        if config.get("config","static") == "True":
            self.recipe.scr_install = a;

    def install_set(self,a):
        if config.get("config","static") == "False":
            self.recipe.scr_install = a;
        else:
            if self.recipe.scr_install == "":
                self.recipe.scr_install = a;
    
    def verify_set(self,a):
        self.recipe.scr_verify = a;
    
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
        self.recipe.git_branch = a;
    
    def gitargs(self,a):
        if debug_en:
            print "gitargs: %s"%(a);
            print "gitbranch: %s"%(a);
        self.recipe.git_args = a;
    
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
        self.recipe.installdir = self.installdir_filter(a);

    def installdir_filter(self, a):
        if str(os.environ.get('PYBOMBS_SDK')) == 'True':
            return a + '_sdk'
        else:
            return a

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
    gitbranchtype = Rep(letter | digit | Any("_-./"))
    revtype = Rep(letter | digit | Any("_-."))
    name = letter + Rep(letter | digit | Any("-"))
    var_name = letter + Rep(letter | digit | Any("_"));
    pkgname = letter + Rep(letter | digit | Any("-.+_"))
    uri = letter + Rep(letter | digit | Any("+@$-._:/"))
    number = Rep1(digit)
    space = Any(" \t\n")
    rspace = Rep(space)
    freetext = Rep(letter | digit | Any("+@$-._:/()#%[]=' ") | Any('"'))
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
        (Str("description:"), Begin("descr")),
        (Str("inherit:"), Begin("inherit")),
        (Str("configuredir:"), Begin("configuredir")),
        (Str("makedir:"), Begin("makedir")),
        (Str("installdir:"), Begin("installdir")),
        (Str("gitbranch:"), Begin("gitbranch")),
        (Str("gitargs:"), Begin("gitargs")),
        (Str("svnrev:"), Begin("svnrev")),
        (Str("gitrev:"), Begin("gitrev")),
        (Str("satisfy_deb:"), Begin("debexpr")),
        (Str("satisfy_rpm:"), Begin("rpmsat")),
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
        State('descr', [
            (sep, IGNORE), (freetext, description_set), (eol, mainstate),
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
        self.description = None;
        self.satisfy_deb = None;
        self.satisfy_rpm = None;
        self.source = [];
        self.install_like = None
        self.category = None;
        self.satisfier = None;
        self.scr_configure = "";
        self.scr_make = "";
        self.scr_install = "";
        self.scr_verify = "";
        self.scr_uninstall = "";
        self.configuredir = "";
        self.makedir = "";
        self.installdir = "";
        self.git_branch = "master";
        self.git_args = "";
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

        # force src satisfaction if in the force_build list
        if(any(self.name in s for s in force_build)):
            self.satisfy_deb = None
            self.satisfy_rpm = None

        # early out if we have already checked this
        if(vars.has_key("%s.satisfier"%(self.name))):
            self.satisfied = vars["%s.satisfier"%(self.name)];
            return True;

        if(any(self.name in s for s in force_pkgs)):
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
        v.print_v(v.PDEBUG, "%s dep [%s]"%(self.name, self.depends))
 
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
        order =  "src" if (self.name in force_build) else vars["satisfy_order"];
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
        v.print_v(v.PDEBUG, "install type priority: " + str(types))
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
        v.print_v(v.PDEBUG, "install deb called (%s)"%(self.name))
        # this is not possible if we do not have deb satisfiers
        if((self.satisfy_deb == None) or ((type(self.satisfy_deb) == type([])) and (len(self.satisfy_deb) == 0))):
            v.print_v(v.PDEBUG, "no deb satisfiers available")
            return False
        elif self.satisfy_deb and not have_debs(self.satisfy_deb):
            v.print_v(v.PDEBUG, "deb is not available locally")
            v.print_v(v.PDEBUG, "check remote repositories...")
            if not debs_exist(self.satisfy_deb):
                return False
        v.print_v(v.INFO, "Installing from .deb: {0}".format(self.name))
        return deb_install(self.satisfy_deb)

    def install_src(self):
        v.print_v(v.PDEBUG, "install src called (%s)"%(self.name))

        # basic source installation requirements
        # install gcc etc before proceeding to build steps
        req = ["gcc"];
        for p in req:
            try:
                if(not global_recipes[p].satisfy()):
                    global_recipes[p].install();
            except:
                return False;

        v.print_v(v.INFO, "Installing from source: {0}".format(self.name))
        state = inv.state(self.name);
        step = 0;
        for i in range( len( self.install_order ) ):
            if( self.install_order[i][0] == state ):
                step = i+1;
        v.print_v(v.PDEBUG, self.install_order)
        # iterate through the install steps of current package
        while(step < len(self.install_order)):
            v.print_v(v.PDEBUG, "Current step: (%s :: %s)"%(self.name, self.install_order[step][0]))
            # run the installation step
            try:
                self.install_order[step][1]();
            except PBRecipeException as e:
                # If any of these fails, we can quit.
                exit(1)
            # update value in inventory
            inv.set_state(self.name, self.install_order[step][0]);
            if(self.install_order[step][0] == "fetch"):
                # if we just fetched a package, store its version and source
                v.print_v(v.PDEBUG, "setting installed version info (%s,%s)"%(self.last_fetcher.used_source,self.last_fetcher.version))
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
            v.print_v(v.WARN, "WARNING: no sources available for package %s!"%(self.name))
            return True
        fetcher = fetch.fetcher(self.source, self);
        fetcher.fetch();
        if(not fetcher.success):
            if(len(self.source) == 0):
                raise PBRecipeException("Failed to Fetch package '%s' no sources were provided! '%s'!"%(self.name, self.source))
            else:
                raise PBRecipeException("Failed to Fetch package '%s' sources were '%s'!"%(self.name, self.source))
        # update value in inventory
        inv.set_state(self.name, "fetch");
        self.last_fetcher = fetcher;
        v.print_v(v.DEBUG, "Setting fetched version info (%s,%s)"%(fetcher.used_source, fetcher.version))
        inv.set_prop(self.name, "source", fetcher.used_source);
        inv.set_prop(self.name, "version", fetcher.version);
     
    def check_stat(self, stat, step):
        if(stat == 0):
            return;
        logging.error('\x1b[31m' + "PyBOMBS %s step failed for package (%s) please see bash output above for a reason (hint: look for the word Error)"%(step, self.name) + '\x1b[0m');
        sys.exit(-1);
   
    def configure(self, try_again=False):
        """
        Run the configuration step for this recipe.
        If try_again is set, it will assume the configuration failed before
        and we're trying to run it again.
        """
        v.print_v(v.PDEBUG, "configure")
        mkchdir(topdir + "/src/" + self.name + "/" + self.installdir)
        if v.VERBOSITY_LEVEL >= v.DEBUG or try_again:
            o_proc = None
        else:
            o_proc = output_proc.OutputProcessorMake(preamble="Configuring: ")
        pre_filt_command = self.scanner.var_replace_all(self.scr_configure)
        st = bashexec(self.scanner.config_filter(pre_filt_command), o_proc)
        if (st == 0):
            return
        # If configuration fails:
        if try_again == False:
            v.print_v(v.ERROR, "Configuration failed. Re-trying with higher verbosity.")
            self.make(try_again=True)
        else:
            v.print_v(v.ERROR, "Configuration failed. See output above for error messages.")
            raise PBRecipeException("Configuration failed")

    def make(self, try_again=False):
        """
        Build this recipe.
        If try_again is set, it will assume the build failed before
        and we're trying to run it again. In this case, reduce the
        makewidth to 1 and show the build output.
        """
        v.print_v(v.PDEBUG, "make")
        mkchdir(topdir + "/src/" + self.name + "/" + self.installdir)
        if v.VERBOSITY_LEVEL >= v.DEBUG or try_again:
            o_proc = None
        else:
            o_proc = output_proc.OutputProcessorMake(preamble="Building:    ")
        # Stash the makewidth so we can set it back later
        makewidth = self.scanner.lvars['makewidth']
        if try_again:
            self.scanner.lvars['makewidth'] = '1'
        st = bashexec(self.scanner.var_replace_all(self.scr_make), o_proc)
        self.scanner.lvars['makewidth'] = makewidth
        if st == 0:
            return
        # If build fails, try again with more output:
        if try_again == False:
            v.print_v(v.ERROR, "Build failed. Re-trying with reduced makewidth and higher verbosity.")
            self.make(try_again=True)
        else:
            v.print_v(v.ERROR, "Build failed. See output above for error messages.")
            raise PBRecipeException("Build failed.")

    def installed(self):
        # perform installation, file copy
        v.print_v(v.PDEBUG, "installed")
        mkchdir(topdir + "/src/" + self.name + "/" + self.installdir)
        if v.VERBOSITY_LEVEL >= v.DEBUG:
            o_proc = None
        else:
            o_proc = output_proc.OutputProcessorMake(preamble="Installing: ")
        pre_filt_command = self.scanner.var_replace_all(self.scr_install)
        st = bashexec(self.scanner.installed_filter(pre_filt_command), o_proc)
        if (st != 0):
            raise PBRecipeException("Installation failed.")

    # run package specific make uninstall
    def uninstall(self):
        try:
            if(self.satisfier == "inventory"):
                mkchdir(topdir + "/src/" + self.name + "/" + self.installdir)
                st = bashexec(self.scanner.var_replace_all(self.scr_uninstall));
                self.satisfier = None;
                del vars["%s.satisfier"%(self.name)]
            else:
                v.print_v(v.WARN, "pkg not installed from source, ignoring")
        except:
            v.print_v(v.DEBUG, "local build dir does not exist")

    # clean the src dir
    def clean(self):
        os.chdir(topdir + "/src/");
        rmrf(self.name);
        inv.set_state(self.name,None);

    def verify(self):
        # perform install verification
        v.print_v(v.INFO, "verify install...")
        mkchdir(topdir + "/src/" + self.name + "/" + self.installdir)
        st = bashexec(self.scanner.var_replace_all(self.scr_verify));
        self.check_stat(st, "Verify");
