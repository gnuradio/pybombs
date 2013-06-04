#!/usr/bin/env python

import ConfigParser;
import os, sys;


def config_init(cfg, reconfig=False):
    cfg_defaults = ConfigParser.RawConfigParser();
    cfg_defaults.read("config.defaults");

    try:
        kl = [];
        vals = {};
        desc = {}
        cfg_source = ""

        if reconfig:
            cfg_source = "config.dat"
            cfg_current = ConfigParser.RawConfigParser();
            cfg_current.read(cfg_source);

            vl = cfg_current.items("config");
            for p in vl:
                kl.append(p[0]);
                vals[p[0]] = p[1];
        else:
            cfg_source = "config.defaults"
            vl = cfg_defaults.items("defaults");
            for p in vl:
                kl.append(p[0]);
                vals[p[0]] = p[1];

        dl = cfg_defaults.items("descriptions");
        for p in dl:
            desc[p[0]] = p[1];
    except:
        print "malformatted " + cfg_source
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


