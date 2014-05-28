#!/usr/bin/env python
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



