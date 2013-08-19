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

import Ice,sys,traceback
Ice.loadSlice("RPCPybombs.ice")
import RPCPybombs;
from mod_pybombs import *;

class ManagerI(RPCPybombs.Manager):
    def __init__(self,name):
        RPCPybombs.Manager.__init__(self)
        print "rpcpybombs manager init (%s)!"%(name)
        recipe_loader.load_all()
        print "recipes loaded..."

    def install(self, pkglist,current=None):
        print "install: %s"%(pkglist);
        for p in pkglist:
            install(p,True);
        return 0;

    def remove(self,pkglist,current=None):
        remove(pkglist);
        return 0;

    def rnd(self,pkglist,current=None):
        remove_nd(pkglist);
        return 0;

    def update(self,pkglist,current=None):
        update(pkglist);
        return 0;

    def list(self,filterlist,current=None):
        cats = get_catpkgs();
        catss = cats.keys();
        catss.sort();
        pl = [];
        for cat in catss:
            cats[cat].sort();
            for pkg in cats[cat]:
                if ((len(filterlist)==0) or any(pkg in s for s in filterlist)):
                    pi = RPCPybombs.PkgInfo()
                    pi.name = pkg;
                    pi.category = cat;
                    pi.version = "";
                    pi.source = "";
                    pi.installed = global_recipes[pkg].satisfy();
                    pi.satisfier = global_recipes[pkg].satisfier;
                    if(pi.satisfier == "inventory"):
                        pi.source = inv.try_get_prop(pkg,"source");
                        pi.version = inv.try_get_prop(pkg,"version");
                    if(not pi.installed):
                        state = "";
                        if(inv.has(pkg)):
                            state = inv.state(pkg);
                            pi.satisfier = "inventory"
                    pl.append(pi);
        return pl;
    

class Server(Ice.Application):
    def run(self, args):
        properties = self.communicator().getProperties()
        # TODO: only set these if they are not provided from passed config
        #self.communicator().getProperties().setProperty("RPCPybombs.Endpoints","tcp -p 8999");
        self.communicator().getProperties().setProperty("RPCPybombs.Endpoints","tcp");
        self.communicator().getProperties().setProperty("Identity","RPCPybombs");
        print self.communicator().getProperties();
        adapter = self.communicator().createObjectAdapter("RPCPybombs")
        id = self.communicator().stringToIdentity(properties.getProperty("Identity"))
        prx = adapter.add(ManagerI(properties.getProperty("Ice.ServerId")), id)
        print "adapter: %s"%(prx);
        adapter.activate()
        self.communicator().waitForShutdown()
        return 0

app = Server()
sys.exit(app.main(sys.argv))
