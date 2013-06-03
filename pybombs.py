#!/usr/bin/env python

# remove this for deployment
import os,re,sys;
files = os.listdir("mod_pybombs");
for f in files:
    if(re.match("\w+.pyc", f)):
        os.unlink("mod_pybombs/" + f)
# remove this for deployment

from mod_pybombs import *
print "---------- loading recipes -------------------"
recipe_loader.load_all()
print "---------- loading recipes finished ----------\n"

if(len(sys.argv) < 2):
    sys.argv.append("help")

if(sys.argv[1] == "search"):
    st = " ".join(sys.argv[2:])
    print "Searching for packages matching: " + st;
    pkg_search(st);

if(sys.argv[1] == "list"):
    print "Printing recipe status list:"
    pkglist()
    print ""

if(sys.argv[1] == "env"):
    print "Writing out env...:"
    writeenv()

if(sys.argv[1] == "install"):
    if(len(sys.argv) < 3):
        sys.argv[1] = "help"
    else:
        for p in sys.argv[2:]:
            install(p,True);

if(sys.argv[1] == "update"):
    if(len(sys.argv) == 2):
        update();
    else:
        update(sys.argv[2:])

if(sys.argv[1] == "rb"):
    if(len(sys.argv) != 3):
        sys.argv[1] = "help"
    else:
        inventory_set(sys.argv[2], "fetch")
        install(sys.argv[2],True)

if(sys.argv[1] == "remove" or sys.argv[1] == "rm" or sys.argv[1] == "uninstall"):
    if(len(sys.argv) < 2):
        sys.argv[1] = "help"
    elif(len(sys.argv) == 2):
        confirm = raw_input("Really remove all installed packages? (y or n) ")
        if(confirm=="y" or confirm=='Y'):
            remove()
        else:
            print "Operation cancelled!"
    else:
        remove(sys.argv[2:])

if(sys.argv[1] == "rnd"):
    if(len(sys.argv) < 3):
        sys.argv[1] = "help"
    else:
        remove_nd(sys.argv[2:])

if(sys.argv[1] == "clean" or sys.argv[1] == "reset"):
    if(len(sys.argv) != 3):
        sys.argv[1] = "help"
    else:
        clean(sys.argv[2])

if(sys.argv[1] == "digraph"):
    graphviz(False)

if(sys.argv[1] == "digraphi"):
    graphviz(True)

if(sys.argv[1] == "info"):
    if(len(sys.argv) != 3):
        sys.argv[1] = "help"
    else:
        pkginfo(sys.argv[2])

if(sys.argv[1] == "config"):
    if(len(sys.argv) == 2):
        config_print()
    elif(len(sys.argv) == 3):
        config_get(sys.argv[2])
    elif(len(sys.argv) == 4):
        config_set(sys.argv[2], sys.argv[3])
    else:
        sys.argv[1] = "help"

if(sys.argv[1] == "inv"):
    if(len(sys.argv) == 2):
        inv.show()
    elif(len(sys.argv) == 3):
        inventory_set(sys.argv[2], None)
    elif(len(sys.argv) == 4):
        inventory_set(sys.argv[2], sys.argv[3])
    else:
        sys.argv[1] = "help"

if(sys.argv[1] == "moo"):
    print "         (__)    "
    print "         (oo)    "
    print "   /------\/     "
    print "  / |    ||      "
    print " *  /\---/\      "
    print "    ~~   ~~      "
    print "....\"Have you mooed today?\"..."

if(sys.argv[1] == "help" or sys.argv[1] == "--help"):
    print "Python Build Overlay Managed Bundle Systems - CLI"
    print "Usage: %s <op> <args...>"%(sys.argv[0])
    print ""
    print " Operations:"
    print "     help            - show this screen"
    print "     list            - show installed & available packages"
    print "     info <pkg>      - display package info"
    print "     install <pkg>   - install a package"
    print "     remove          - cleanly remove all fully installed packages and dependents"
    print "     remove <pkg>    - cleanly remove a fully installed package and dependents"
    print "     rnd <pkg>       - cleanly remove a fully installed package (*DANGER* can break dependees!)"
    print "     clean <pkg>     - ensure a package is in the uninstalled state"
    print "     config          - show all local config settings"
    print "     config <k>      - show one local config setting"
    print "     config <k> <v>  - set a local config setting"
    print "     inv             - show inventory values"
    print "     inv <k>         - clear inventory value for k"
    print "     inv <k> <v>     - update local package k inventory value to v"
    print "     digraph         - write out package.dot digraph for graphviz (all pkgs)"
    print "     digraphi        - write out package.dot digraph for graphviz (installed pkgs)"
    print "     env             - write out env"
    print "     update          - update all packages"
    print "     update <pkg>    - update a specific package"
    print "     rb <pkg>        - rebuild without re-fetch (equivalent to [inv pkg fetch && install pkg])"
    print "     search <expr>   - search for a package recipe matching <expr>"
    print ""

#if(sys.argv
#op = sys.argv[1];

#a = check_installed("uhd");
#install("uhd",True);
#install("gnuradio",True);

#print global_recipes
