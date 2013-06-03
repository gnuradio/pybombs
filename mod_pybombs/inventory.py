#!/usr/bin/env python

import pickle,os;
topdir = os.path.split(os.path.realpath(__file__))[0] + "/../";
import exceptions;

class inventory:
    def __init__(self):
        self.inv_file = "inventory.dat";
        self.contents = {};
        self.loadc();

    def has(self, pkg):
        return self.contents.has_key(pkg);

    def loadc(self):
        os.chdir(topdir);
        try:
#            print "attempting to load existing inventory"
            f = open(self.inv_file, 'rb')
            self.contents = pickle.load(f)
            f.close()
        except:
            print "no existing inventory found, creating an empty one..."
            self.contents = {};
#        print "loaded: %s"%(self.contents);
 
    def savec(self):
        os.chdir(topdir);
        output = open(self.inv_file, 'wb')
        pickle.dump(self.contents, output)
        output.close()

    def state(self,pkg):
        self.loadc();
        try:
            return self.contents[pkg]["state"];
        except:
            return None;

    def set_state(self,pkg,state):
        self.loadc();
        if(state):
            if(not self.has(pkg)):
                self.contents[pkg] = {};
            self.contents[pkg]["state"] = state;
        else:
            try:
                del self.contents[pkg];
            except:
                pass
        self.savec();

    def set_prop(self,pkg,prop,val):
        self.loadc();
        if(not self.has(pkg)):
            raise exceptions.NameError("package has no inv entry" + str((pkg,prop)));
        self.contents[pkg][prop] = val;
        self.savec();

    def get_prop(self,pkg,prop):
        self.loadc();
        if(not self.has(pkg)):
            raise exceptions.NameError("package has no inv entry" + str((pkg,prop)));
        if(not self.contents[pkg].has_key(prop)):
            raise exceptions.NameError("package in inv does not have prop" + (pkg,prop));
        return self.contents[pkg][prop];

    def try_get_prop(self,pkg,prop):
        try:
            return self.get_prop(pkg,prop);
        except:
            print "fail"
            return None;

    def clear_props(self,pkg):
        self.loadc();
        self.contents[pkg] = {"state":self.contents[pkg]["state"]};
        self.savec();

    def show(self):
        print self.contents;


