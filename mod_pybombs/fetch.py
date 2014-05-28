#!/usr/bin/env python

from globals import *
import re,sys;
from sysutils import *;

class fetch:
    def __init__(self, source, recipe):
        self.recipe = recipe;
        self.success = False;

        # try all the sources until one works?
        for s in source:
            if(self.try_fetch(s)):
                self.success = True;
                self.used_source = s;
                break;

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

