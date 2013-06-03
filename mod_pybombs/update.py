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

class update:
    def __init__(self, r):
        self.r = r;
        self.pkg = self.r.name;

    def check(self):
        if(not global_recipes[self.pkg].satisfier == "inventory"):
            return True;

        # look up current version
        self.cv = inv.get_prop(self.pkg, "version");
        installed_source = inv.get_prop(self.pkg, "source");
        self.s = installed_source;
        #print installed_source;
        
        # Check #1 :: the installed source exists in the recipe
        sourcematch = False;
        for s in self.r.source:
            if(s == installed_source):
                sourcematch = True;
        if(not sourcematch):
            return False;

        # Check #2 :: source specific checks
        r = re.search(r'(\w+)://',installed_source);
        ft =  r.group(1); # fetch type
        if(ft == "wget"):
            return True;  # ignore md5 sum for now, URI has already matched
        if(ft == "file"): 
            return self.check_file();
        if(ft == "git"):
            return self.check_git();
        if(ft == "svn"):
            return self.check_svn();
        die("unknown source type: %s"%(installed_source));
    


    def check_file(self):
        path = self.s[7:];
        nv = filemd5(path);
        return self.cv == nv;
        
    def check_git(self):
        loc = self.s[6:]

        # Get Check #1 -- is the gitref equal to the current installed hash?
        if(self.r.gitrev == self.cv):
            assert(not (self.cv == ""));
            return True;

        # at this point we are going to need some info from the remote repo
        nv = shellexec(["git","ls-remote",loc]);
#        print nv;

        # Git Check #2 -- gitrev is specified it must be a TAG or non-matching hash
        if(not (self.r.gitrev == "")):
            # look for a matching tag
            rs = re.search(("^([0-9a-f]+)\s+refs/tags/%s$"%(self.r.gitrev)), nv, re.MULTILINE);
            if(rs):  # if we match a tag
                newhash = rs.group(1);
                if(newhash == self.cv):
                    # hash matches the given tag
                    return True;
                else:
                    # hash doesnt match the given tag
                    return False;
            else:
                # gitrev did not match a tag, assume it was a hash that did not match above!
                return False;

        # Git Check #3 -- branch HEAD hash matches?
        branch = self.r.gitbranch;
        if(branch == ""):
            branch = "master";
        rs = re.search(("^([0-9a-f]+)\s+refs/heads/%s$"%(branch)), nv, re.MULTILINE);
        if(not rs):
            die("remote branch %s does not exist on %s!"%(branch, self.s));
        newhash = rs.group(1);
        if(newhash == self.cv):
            # hash of the head matches
            return True;
        else:
            # hash of the head doesnt match
            return False;

    def check_svn(self):
        loc = self.s[6:]
        nv = shellexec(["git","ls-remote",loc])
        print nv;

        print "WARNING: SVN update is broken"
        print "WARNING: SVN update is broken"
        print "WARNING: SVN update is broken"
        print "WARNING: SVN update is broken"

        return False;

