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
if(len(sys.argv) <= 1):
    print "usage: %s -h host -p port"%(sys.argv[0])
    sys.exit(-1);

comm = Ice.initialize()
prox = "RPCPybombs:tcp %s"%(" ".join(sys.argv[1:]));
print prox;
mgr = RPCPybombs.ManagerPrx.checkedCast(comm.stringToProxy(prox));
print mgr.list([]);
#print mgr.list(["gnuradio"]);
#mgr.install(["gnuradio"]);



