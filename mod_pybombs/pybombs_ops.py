
import sys;
from globals import *;
from sysutils import *;
from inventory import *

def list_unique_ord(seq): 
   # order preserving
   checked = []
   for e in seq:
       if e not in checked:
           checked.append(e)
   return checked

def pkg_search(query):
    for p in global_recipes.keys():
        if re.search(query, p):
            print " * " + str(p);
    
def check_recipe(pkgname):
    return global_recipes.has_key(pkgname)

def check_installed(pkgname):
    print "checking for "+pkgname;
    #print pkgname + " not installed"
    print global_recipes[pkgname].satisfy()
    return global_recipes[pkgname].satisfy();

def install(pkgname, die_if_already=False):
    if not check_recipe(pkgname):
        die("unknown package "+pkgname);
    if die_if_already and check_installed(pkgname):
        print pkgname + " already installed";
        return;
    print "installing "+pkgname;

    rc = global_recipes[pkgname];
    pkg_missing = rc.recursive_satisfy();

    # remove duplicates while preserving list order (lowest nodes first)
    pkg_missing = list_unique_ord(pkg_missing);

    print "packages to install: " + str(pkg_missing);

    # prompt if list is ok?
    # provide choice of deb satisfiers or source build?

    for pkg in pkg_missing:
        global_recipes[pkg].install();

#    global_recipes[pkgname].install();

def graphviz(installed_only=False):
    if(not check_installed("graphviz")):
        install("graphviz",True);
    f = open("digraph.dot","w");
    f.write("digraph g {\n");
    for pkg in global_recipes.keys():
        p = global_recipes[pkg];
        if((not installed_only) or (p.satisfy())):
            f.write("%s [label=\"%s\"]\n"%(pkg.replace("-","_"),pkg.replace("-","_")));
        for d in p.depends:
            if((not installed_only) or (p.satisfy())):
                f.write( "%s -> %s\n"%(pkg.replace("-","_"), d.replace("-","_")) );   
    f.write("}\n");
    f.close();
    print "digraph.dot written"
    os.chdir(topdir);
    bashexec("dot digraph.dot -Tpng -odigraph.png");
    print "png written"
    bashexec("eog digraph.png");
    print "done"
    

def get_catpkgs():
    pkglist = global_recipes.keys();
    pkglist.sort();

    cats = {};
    for pkg in pkglist:
        c = global_recipes[pkg].category;
        if(not cats.has_key(c)):
            cats[c] = [];
        cats[c].append(pkg);

    return cats;




def pkglist():
    
    cats = get_catpkgs();
    print cats;
    catss = cats.keys();
    catss.sort();
    
    for cat in catss:
        print "Category: %s"%(cat)
        cats[cat].sort();
        for pkg in cats[cat]:
            version = "";
            source = "";
            installed = global_recipes[pkg].satisfy();
            satisfier = global_recipes[pkg].satisfier;
            if(satisfier == "inventory"):
                source = inv.try_get_prop(pkg,"source");
                version = inv.try_get_prop(pkg,"version");
        
            if(installed):
                #print "%25s %12s %10s"%( pkg, "installed", satisfier );
                print "%25s %12s %10s %20s %s"%( pkg, "installed", satisfier, version, source );
            else:
                state = "";
                if(inv.has(pkg)):
                    state = inv.state(pkg);
                    satisfier = "inventory"
                print "%25s %12s %10s %20s %s"%( pkg, state, satisfier, version, source );

def pkginfo(pn):
    try:
        pkg = global_recipes[pn];
    except:
        die("package not found");

    print "Package Info for:    %s"%(pkg.name);
    print "Package Category:    %s"%(pkg.category);
    print "Package Deps:        %s"%(str(pkg.depends));
    
    print "";
    print "Package Source:      %s"%(str(pkg.source));
       
def inventory_set(k,v):
    inv.set_state(k,v);

def config_print():
    cv = config.items("config");
    for p in cv:
        print p[0] + " = " +  p[1];

def config_get(k):
    print config.get("config",k);

def config_set(k,v):
    config.set("config",k,v);
    config_write(config);
    print "value updated"

def clean(k):
    try:
        pkg = global_recipes[k];
    except:
        die("package not found: %s"%(k));
    pkg.clean();
    print "cleaned local "+k;

# remove packages in list k and all of their dependents
def remove(pkglist=None):
    nk = [];
    inv = inventory()
    
    if(pkglist == None):
        cats = get_catpkgs();
        catss = cats.keys();
        catss.sort();
        for cat in catss:
            #print "Category: %s"%(cat)
            cats[cat].sort();
            for pkg in cats[cat]:
                nk.append(pkg);
                
    else:
        for pkg in pkglist:
            nk.append(pkg);
          
    # determine all dependent packages to remove        
    rblist = [];                
    for p in nk:  # find all packages that depend on the list
        pkg = global_recipes[p];
        rblist.append(p);
        rblist.extend(pkg.get_dependents());
    rblist = list(set(rblist)); # uniquefy the list
    #print rblist;
    
    rmlist = [];
    # remove currently uninstalled packages from list of pkgs
    for p in rblist:
        if(not global_recipes[p].satisfy()):
            rmlist.append(p);
        elif not inv.has(p):
            rmlist.append(p)
    for p in rmlist:
            rblist.remove(p);
    #print rblist;               

    # remove effected packages            
    print "\nRemoving the following packages: " + str(rblist)
    if rblist == []:
        print "\nNothing to do!"
        return
    confirm = raw_input("\nContinue (y or n) ")
    if(confirm=="y" or confirm=='Y'):
        for p in rblist: # 
            try:
                pkg = global_recipes[p];
            except:
                die("package not found: %s"%(p));
            pkg.uninstall();
            print "uninstalled "+p;
            clean(p);
    else:
        print "Operation cancelled!"

# remove packages in list k and NONE of thier dependents
def remove_nd(k):
    for p in k:
        try:
            pkg = global_recipes[p];
        except:
            die("package not found: %s"%(p));
        pkg.uninstall();
        print "uninstalled "+p;
        clean(p);

# Update packages with PyBOMBS ;-D
def update(pkglist=None):
    outofdate = [];

    # check all packages, or specified packages for up-to-date-ness
    if(pkglist == None):
        cats = get_catpkgs();
        catss = cats.keys();
        catss.sort();
        for cat in catss:
            print "Category: %s"%(cat)
            cats[cat].sort();
            for pkg in cats[cat]:
                r = global_recipes[pkg];
                nv = r.newest_version();
                print "%25s nv: %s"%(pkg, nv);
                if(not nv):
                    outofdate.append(pkg);
    else:
        for pkg in pkglist:
            r = global_recipes[pkg];
            nv = r.newest_version();
            print "%25s nv: %s"%(pkg, nv);
            if(not nv):
                outofdate.append(pkg);

    print "Packages out of date: " + str(outofdate);

    # determine all dependent packages to remove
    rblist = [];
    for p in outofdate:  # find all packages that depend on the list
        pkg = global_recipes[p];
        rblist.append(p);
        rblist.extend(pkg.get_dependents());
    rblist = list(set(rblist)); # uniquefy the list

#    print rblist;
    rmlist = [];
    # remove currently uninstalled packages from list of remove-install pkgs
    for p in rblist:
        if(not global_recipes[p].satisfy()):
            rmlist.append(p);
    for p in rmlist:
            rblist.remove(p);
#    print rblist;
            
    # make sure this is ok
    print "Will remove and install the following packages to the latest version: %s"%(str(rblist));
    confirm = raw_input("\nContinue (y or n) ")
    if(confirm=="y" or confirm=='Y'):
        pass
    else:
        print "aborting"
        sys.exit(-1);

    # remove effected packages
    print "removing the following packages: " + str(rblist);
    remove_nd(rblist);

    # install effected packages
    print "installing the following packages: " + str(rblist);
    for p in rblist:
        install(p);

def writeenv():
    f = open(vars["prefix"] + "/setup_env.sh","w");
    f.write("export %s=\"%s\"\n"%("PATH",env["PATH"]));
    f.write("export %s=\"%s\"\n"%("PYTHONPATH",env["PYTHONPATH"]));
    f.write("export %s=\"%s\"\n"%("LD_LIBRARY_PATH",env["LD_LIBRARY_PATH"]));
    f.write("export %s=\"%s\"\n"%("PKG_CONFIG_PATH",env["PKG_CONFIG_PATH"]));
    f.close();
    

