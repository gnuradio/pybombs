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

import re;

debug_en = False;

# copy initial variable values from cfg
def vars_init(cfg):
    vars = {};
    for kv in cfg.items("config"):
        vars[kv[0]] = kv[1];
    return vars;
 

def vars_copy(v1):
    v2 = {};
    for k in v1.keys():
        v2[k] = v1[k];
    if debug_en:
        print "vars_copy %s -> %s"%(v1,v2);
    return v2;

def vars_defaults(v):
    assert(v.has_key("prefix"));
    #v["prefixre"] = re.escape(v["prefix"]).replace("/","\/");
    v["reprefix"] = re.escape(v["prefix"]);
    # set global derived defaults here
    return v;
 

