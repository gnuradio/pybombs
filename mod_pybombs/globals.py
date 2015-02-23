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

import sys, os, errno, subprocess
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

# initialize cfg if need be
if(len(cfg) == 0):
    config_init(config);
    config_write(config);

# make sure we are not missing values that have been added to defaults file
config_desc = ConfigParser.RawConfigParser();
config_desc.read("config.defaults");
for v in config_desc.options("defaults"):
    defa = config_desc.get("defaults",v);
    try:
        desc = config_desc.get("descriptions",v);
    except:
        desc = None
    if not v in config.options("config"):
        print "Found new missing default value in your config.dat:"
        if desc:
            print desc;
        rv = raw_input("%s [%s]:"%(v,defa));
        if not rv:
            rv = defa;
        config.set("config", v, rv);
        config_write(config);
if str(os.environ.get('PYBOMBS_SDK')) == 'True':
    #deal with additional, sdk-specific configuration
    for v in config_desc.options("sdk"):
        defa = config_desc.get("sdk",v);
        try:
            desc = config_desc.get("sdk_descriptions",v);
        except:
            desc = None
        if not v in config.options("config"):
            print "Found new missing default value in your config.dat:"
            if desc:
                print desc;
            rv = raw_input("%s [%s]:"%(v,defa));
            if not rv:
                rv = defa;
            config.set("config", v, rv);
            config_write(config);
    config.set("config", "forcepkgs", config.get("config", "sdk_forcepkgs"));
    config.set("config", "forcebuild", config.get("config", "sdk_forcebuild"));
    config.set("config", "satsify_order", config.get("config", "sdk_satisfy_order"));
    config.set("config", "prefix", config.get("config", "sandbox") + config.get("config", "sdk_prefix"));
    #set environment...
    command = ['bash', '-c', 'source ' + config.get('config', 'env') + '  && env']

    proc = subprocess.Popen(command, stdout = subprocess.PIPE)

    for line in proc.stdout:
        (key, _, value) = line.partition("=")
        os.environ[key] = value.replace('\n', '')

    proc.communicate()
    
    

# set up the force list
force_pkgs = [];
try:
    fl = config.get("config","forcepkgs");
    force_pkgs = re.sub(r' ', r'', fl).split(",")
except:
    pass

force_build = [];
try:
    fl = config.get("config","forcebuild");
    force_build = re.sub(r' ', r'', fl).split(",")
except:
    pass

#give static a default value
config.set("config","static","False")

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
        path = os.path.expanduser(path)
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
if str(os.environ.get('PYBOMBS_SDK')) == 'True':
    inv = inventory(str(config.get('config', 'inv')));
    written_env = env_init(vars, 'device_prefix');
    destination_key = 'sandbox'
else:
    inv = inventory();
    written_env = env;
    destination_key = 'prefix'

def die(s):
    print s;
    sys.exit(-1);



