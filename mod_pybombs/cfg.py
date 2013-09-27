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
        if kn == "gituser":
            if os.environ.get("USER"):
                vals[kn] = os.environ.get("USER");
        if kn == "prefix":
            pwd = os.environ.get("PWD");
            if os.path.basename(pwd)=="pybombs":
                vals[kn] = os.path.join(os.path.dirname(pwd), "target")

        rv = raw_input("%s [%s]:"%(kn,vals[kn]));
        if not rv:
            rv = vals[kn];
        cfg.set("config", kn, rv);

    print "done"


def config_write(config):
    # Need to use 'w' so that we overwrite any old config.
    a = open('config.dat','wb');
    config.write(a);
    a.close();


