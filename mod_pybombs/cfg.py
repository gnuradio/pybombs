#!/usr/bin/env python

import ConfigParser;
import sys;

def config_init(cfg):
    dcfg = ConfigParser.RawConfigParser();
    dcfg.read("config.defaults");
    try:
        kl = [];
        vals = {};
        desc = {}
        vl = dcfg.items("defaults");
        dl = dcfg.items("descriptions");
        for p in vl:
            kl.append(p[0]);
            vals[p[0]] = p[1];
        for p in dl:
            desc[p[0]] = p[1];

    except:
        print "malformatted config.defaults"
        sys.exit(-1);


    print "Initializing config file..."
    cfg.add_section("config");
    for kn in kl:
        if(desc.has_key(kn)):
            print desc[kn];
        rv = raw_input("%s [%s]:"%(kn,vals[kn]));
        if not rv:
        #if rv == "":
            rv = vals[kn];
        cfg.set("config", kn, rv);
    
    print "done"


def config_write(config):
    a = open('config.dat','wb');
    config.write(a);
    a.close();


