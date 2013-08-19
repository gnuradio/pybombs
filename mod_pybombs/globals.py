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

import sys, os, errno
from inventory import *
import ConfigParser
from cfg import *
from vars import *
from env import *

# needed for 2.4 support
try:
    any
except NameError:
    def any(s):
        for v in s:
            if v:
                return True
        return False

# remember top path...
topdir = os.path.split(os.path.realpath(__file__))[0] + "/../";

# load config values
config = ConfigParser.RawConfigParser();
cfg = config.read("config.dat");
if(len(cfg) == 0):
    config_init(config);
    config_write(config);

# set up the force list
force_list = [];
try:
    fl = config.get("config","forcepkgs");
    force_list = re.sub(r' ', r'', fl).split(",")
except:
    pass

# make sure a few directories exist
prefix = config.get("config", "prefix").rstrip('/')
print "Settled on prefix: " + prefix
pathcheck = [topdir + "src", prefix, prefix + "/lib64",
                prefix + "/lib/", prefix + "/lib/python2.7/",
                prefix + "/lib/python2.6/", prefix + "/lib/python2.6/site-packages",
                prefix + "/lib64/python2.6/", prefix + "/lib64/python2.6/site-packages",
                prefix + "/lib/python2.7/site-packages", prefix + "/share/", 
                prefix + "/share/sip/"]

try:
    for path in pathcheck:
        if(not os.path.exists(path)):
            os.mkdir(path);
except OSError, error:
    if error.errno == errno.EACCES:
        print "\n" + str(error)
        print("Error! Configured install prefix requires root privileges. Please re-run as sudo!")
        exit(error.errno)


vars = vars_init(config);
vars = vars_defaults(vars);

env = env_init(vars);

global_recipes = {};
inv = inventory();

def die(s):
    print s;
    sys.exit(-1);



