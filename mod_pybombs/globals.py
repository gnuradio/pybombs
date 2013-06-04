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



