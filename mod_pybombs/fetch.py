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

from globals import *
import re,sys;
from sysutils import *;

class fetcher:
    def __init__(self, source, recipe):
        self.source = source;
        self.recipe = recipe;
        self.success = False;

    def fetch(self):
        # try all the sources until one works?
        for s in self.source:
            if(self.try_fetch(s)):
                self.success = True;
                self.used_source = s;
                break;

    def fetched(self):
        for s in self.source:
            if(self.check_fetched(s)):
                return True
        return False

    def check_fetched(self, s):
        r = re.search(r'(\w+)://',s);
        ft = r.group(1); # fetch type
        if(ft == "wget"):
            url = s[7:];
            fdir,fname = os.path.split(url);
            return os.path.exists(os.path.join(topdir, "src", fname))
        elif(ft == "file"):
            path = s[7:]
            fdir,fname = os.path.split(path);
            return os.path.exists(os.path.join(topdir, "src", fname))
        elif(ft == "git"):
            return os.path.exists(os.path.join(topdir, "src", self.recipe.name))
        elif(ft == "svn"):
            return os.path.exists(os.path.join(topdir, "src", self.recipe.name))
        die("unknown source type: %s"%(s))

    def try_fetch(self, s):
        r = re.search(r'(\w+)://',s);
        ft =  r.group(1); # fetch type
        if(ft == "wget"):
            return self.fetch_wget(s);
        elif(ft == "file"):
            return self.fetch_file(s);
        elif(ft == "git"):
            return self.fetch_git(s);
        elif(ft == "svn"):
            return self.fetch_svn(s);
        die("unknown source type: %s"%(s));

    def fetch_wget(self,s):
        url = s[7:];
        fdir,fname = os.path.split(url);
        os.chdir(topdir + "/src/");
        try_unlink(fname);
        stat = shellexec_shell("wget --no-check-certificate --timeout=10 %s"%(url), False);

        # store our current version
        self.version = filemd5(fname);
        if(stat != 0):
            return False;
        return self.extract(fname);

    def fetch_file(self,s):
        path = s[7:];
        fdir,fname = os.path.split(path);
        os.chdir(topdir);
        try:
            os.stat(path);
        except:
            print "%s not found"%(s);
            return False;
        if(not path[0] == "/"):
            path = "../" + path;
        try_unlink(topdir + "/src/" + fname);
        os.symlink(path, topdir + "/src/" + fname);

        # store our current version
        self.version = filemd5(fname);
        return self.extract(fname);

    def fetch_git(self,s):
        loc = s[6:]
        os.chdir(topdir + "/src/");
        stat = shellexec_shell("git clone -b %s %s %s"%(self.recipe.gitbranch, loc, self.recipe.name), False);
        if(stat != 0):
            return False;
        
        os.chdir(topdir + "/src/" + self.recipe.name);
        if(self.recipe.gitrev != ""):
            stat = shellexec_shell("git checkout %s"%(self.recipe.gitrev), False);
            if(stat != 0):
               return False;
    
        # store our current version
        out1 = shellexec(["git","rev-parse","HEAD"]);
        rm = re.search("([0-9a-f]+).*",out1);
        self.version = rm.group(1);
        return True;

    def fetch_svn(self,s):
        loc = s[6:]
        os.chdir(topdir + "/src/");
        stat = shellexec_shell("svn co -r %s %s %s"%(self.recipe.svnrev, loc, self.recipe.name), False);
        if(stat != 0):
            return False;

        # store our current version
        out1 = shellexec(["svnversion",topdir + "/src/" + self.recipe.name]);
        rm = re.search("\d*:*(\d+).*",out1);
        self.version = rm.group(1);
        return True;

    def extract(self,fn):
        os.chdir(topdir + "/src/");
        print "Extract %s"%(fn);
        if(re.match(r'.*\.tar.gz', fn) or re.match(r'.*\.tgz', fn)):
            out = shellexec(["tar tbzB 1 --file %s"%(fn)]);
            dirname = out.strip().split("/")[0];
            stat = shellexec_shell("tar xzf %s"%(fn), False);
            if(stat != 0):
                return False;
            rmrf(self.recipe.name);
            os.rename(dirname, self.recipe.name);
        elif(re.match(r'.*\.tar.bz2?', fn) or re.match(r'.*\.tbz2?', fn)):
            out = shellexec(["tar tbjB 1 --file %s"%(fn)]);
            dirname = out.strip().split("/")[0];
            stat = shellexec_shell("tar xjf %s"%(fn), False);
            if(stat != 0):
                return False;
            rmrf(self.recipe.name);
            os.rename(dirname, self.recipe.name);

        else:
            print "unknown compression type?"%(fn);
            return False;
        os.unlink(fn);
        return True;

