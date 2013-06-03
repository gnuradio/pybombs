import sys,os;
from inventory import *
import ConfigParser;
from cfg import *
from vars import *
from env import *;

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
pathcheck = [topdir + "src", config.get("config","prefix"), config.get("config", "prefix") + "/lib64",
    config.get("config", "prefix") + "/lib/", config.get("config", "prefix") + "/lib/python2.7/", 
    config.get("config", "prefix") + "/lib/python2.6/", config.get("config", "prefix") + "/lib/python2.6/site-packages",
    config.get("config", "prefix") + "/lib64/python2.6/", config.get("config", "prefix") + "/lib64/python2.6/site-packages",
    config.get("config", "prefix") + "/lib/python2.7/site-packages", config.get("config", "prefix") + "/share/", 
    config.get("config", "prefix") + "/share/sip/"];
for path in pathcheck:
    if(not os.path.exists(path)):
        os.mkdir(path);

vars = vars_init(config);
vars = vars_defaults(vars);

env = env_init(vars);

global_recipes = {};
inv = inventory();

def die(s):
    print s;
    sys.exit(-1);



