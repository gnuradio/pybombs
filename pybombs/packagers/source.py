#
# Copyright 2015 Free Software Foundation, Inc.
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
"""
Packager: Source packages
"""

import subprocess
from pybombs import pb_logging
from pybombs import inventory
from pybombs.config_manager import config_manager
from pybombs.packagers.base import PackagerBase

class Source(PackagerBase):
    def __init__(self):
        PackagerBase.__init__(self)
        if self.cfg.get_active_prefix().prefix_dir is None:
            self.log.error("No prefix specified. Aborting.")
            exit(1)
        self.prefix = self.cfg.get_active_prefix()
        self.inventory = inventory.Inventory(self.prefix.inv_file)
        self.inventory.load()

    def exists(self, recipe, throw_ex=True):
        """
        This will work whenever any sources are defined.
        """
        return len(recipe.srcs) > 0


    def install(self, name, throw_ex=True):
        """
        Run the installation process for package 'name'.

        May raise an exception if things go terribly wrong.
        Otherwise, return True on success and False if installing
        failed in an expected manner (e.g. the package wasn't available
        by this package manager).
        """
        raise NotImplementedError()

    def installed(self, name, throw_ex=True):
        """
        We read the version number from the inventory. It might not exist,
        but that's OK.
        """
        if self.inventory.has(name) and self.inventory.get_state(name) == 'installed':
            return self.inventory.get_version(name, True)
        return False


#import pb_logging

#class SrcManager(object):
    #def __init__(self):
        #self.log = pb_logging.logger.getChild("SrcManager")
        #self.cfg = config_manager.config_manager
        #self.prefix = self.cfg.get_active_prefix()
        #self.inventory = inventory.Inventory(self.prefix.inv_file)
        #self.inventory.load()


    #def is_installed(self, recipe):
        #"""
        #Check if a package is installed.
        #"""
        #return self.inventory.get_state(recipe.id) == 'installed'

    #def remove(self, recipe):
        #pass # tbw

    #def install(self, recipe):
        #pass


    #def fetch(self):
        #pass
        ### this is not possible if we do not have sources
        ##if(len(self.source) == 0):
            ##v.print_v(v.WARN, "WARNING: no sources available for package %s!"%(self.name))
            ##return True
        ##fetcher = fetch.fetcher(self.source, self)
        ##fetcher.fetch()
        ##if(not fetcher.success):
            ##if(len(self.source) == 0):
                ##raise PBRecipeException("Failed to Fetch package '%s' no sources were provided! '%s'!"%(self.name, self.source))
            ##else:
                ##raise PBRecipeException("Failed to Fetch package '%s' sources were '%s'!"%(self.name, self.source))
        ### update value in inventory
        ##inv.set_state(self.name, "fetch")
        ##self.last_fetcher = fetcher
        ##v.print_v(v.DEBUG, "Setting fetched version info (%s,%s)"%(fetcher.used_source, fetcher.version))
        ##inv.set_prop(self.name, "source", fetcher.used_source)
        ##inv.set_prop(self.name, "version", fetcher.version)


    #def configure(self, recipe, try_again=False):
        #"""
        #Run the configuration step for this recipe.
        #If try_again is set, it will assume the configuration failed before
        #and we're trying to run it again.
        #"""
        #self.log.debug("Configuring recipe {}".format(recipe.id))
        ##mkchdir(topdir + "/src/" + self.name + "/" + self.installdir)
        ##if v.VERBOSITY_LEVEL >= v.DEBUG or try_again:
            ##o_proc = None
        ##else:
            ##o_proc = output_proc.OutputProcessorMake(preamble="Configuring: ")
        ##pre_filt_command = self.scanner.var_replace_all(self.scr_configure)
        ##st = bashexec(self.scanner.config_filter(pre_filt_command), o_proc)
        ##if (st == 0):
            ##return
        ### If configuration fails:
        ##if try_again == False:
            ##v.print_v(v.ERROR, "Configuration failed. Re-trying with higher verbosity.")
            ##self.make(try_again=True)
        ##else:
            ##v.print_v(v.ERROR, "Configuration failed. See output above for error messages.")
            ##raise PBRecipeException("Configuration failed")


    #def make(self, try_again=False):
        #"""
        #Build this recipe.
        #If try_again is set, it will assume the build failed before
        #and we're trying to run it again. In this case, reduce the
        #makewidth to 1 and show the build output.
        #"""
        #self.log.debug("Building recipe {}".format(recipe.id))
        ##v.print_v(v.PDEBUG, "make")
        ##mkchdir(topdir + "/src/" + self.name + "/" + self.installdir)
        ##if v.VERBOSITY_LEVEL >= v.DEBUG or try_again:
            ##o_proc = None
        ##else:
            ##o_proc = output_proc.OutputProcessorMake(preamble="Building:    ")
        ### Stash the makewidth so we can set it back later
        ##makewidth = self.scanner.lvars['makewidth']
        ##if try_again:
            ##self.scanner.lvars['makewidth'] = '1'
        ##st = bashexec(self.scanner.var_replace_all(self.scr_make), o_proc)
        ##self.scanner.lvars['makewidth'] = makewidth
        ##if st == 0:
            ##return
        ### If build fails, try again with more output:
        ##if try_again == False:
            ##v.print_v(v.ERROR, "Build failed. Re-trying with reduced makewidth and higher verbosity.")
            ##self.make(try_again=True)
        ##else:
            ##v.print_v(v.ERROR, "Build failed. See output above for error messages.")
            ##raise PBRecipeException("Build failed.")

    ##def installed(self):
        ### perform installation, file copy
        ##v.print_v(v.PDEBUG, "installed")
        ##mkchdir(topdir + "/src/" + self.name + "/" + self.installdir)
        ##if v.VERBOSITY_LEVEL >= v.DEBUG:
            ##o_proc = None
        ##else:
            ##o_proc = output_proc.OutputProcessorMake(preamble="Installing: ")
        ##pre_filt_command = self.scanner.var_replace_all(self.scr_install)
        ##st = bashexec(self.scanner.installed_filter(pre_filt_command), o_proc)
        ##if (st != 0):
            ##raise PBRecipeException("Installation failed.")

    ### run package specific make uninstall
    ##def uninstall(self):
        ##try:
            ##if(self.satisfier == "inventory"):
                ##mkchdir(topdir + "/src/" + self.name + "/" + self.installdir)
                ##st = bashexec(self.scanner.var_replace_all(self.scr_uninstall))
                ##self.satisfier = None
                ##del vars["%s.satisfier"%(self.name)]
            ##else:
                ##v.print_v(v.WARN, "pkg not installed from source, ignoring")
        ##except:
            ##v.print_v(v.DEBUG, "local build dir does not exist")

    ### clean the src dir
    ##def clean(self):
        ##os.chdir(topdir + "/src/")
        ##rmrf(self.name)
        ##inv.set_state(self.name,None)


    ##def run_install(self, pkgname):
        ##"""
        ##Install the package called pkgname.

        ##Order of ops for each pkgname:
        ##- Check if pkgname is in the recipe list
        ##- Ask for a Recipe object and see if it's already installed
          ##- If yes, figure out if we want to reinstall
            ##- If no, return
        ##- Ask the RecipeListManager for a list of dependencies (recursively)
        ##- For every dependency, ask Recipe if it's already installed in
          ##the current prefix
        ##- Create a new list of all Recipes that need to be installed
        ##- Install each of these
        ##"""
        ##self.log.info("Starting installation of package {0}".format(pkgname))


        ##if not check_recipe(pkgname):
            ##die("unknown package "+pkgname);
        ##if die_if_already and check_installed(pkgname):
            ##print pkgname + " already installed";
            ##return;
        ##validate_write_perm(vars["prefix"])
        ##rc = global_recipes[pkgname];
        ##pkg_missing = rc.recursive_satisfy();

        ### remove duplicates while preserving list order (lowest nodes first)
        ##pkg_missing = list_unique_ord(pkg_missing);
        ##self.log.info("Installing packages:\n" + "\n".join(["* {0}".format(x) for x in pkg_missing]))

        ### prompt if list is ok?
        ### provide choice of deb satisfiers or source build?

        ##for pkg in pkg_missing:
            ##global_recipes[pkg].install();
            ##if(pkg == "gnuradio"):
                ##if(confirm("Run VOLK Profile to choose fastest kernels?","Y",5)):
                    ##run_volk_profile();
    ###    global_recipes[pkgname].install();
