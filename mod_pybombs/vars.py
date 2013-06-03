#!/usr/bin/env python
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
 

