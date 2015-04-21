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
""" PyBOMBS command: Install """

from pybombs.commands import *
from pybombs import pb_logging
#import pybombs_ops as pybombs_ops
from pybombs import simple_tree

class PyBombsInstall(PyBombsCmd):
    """ Install a package """
    cmds = {
            'install': 'Install a package'
    }

    def __init__(self, cmd=None):
        PyBombsCmd.__init__(self, cmd)

    def setup_parser(self):
        " Add 'install' specific flags "
        parser = PyBombsCmd.setup_parser(self)
        ogroup = OptionGroup(parser, "Install options")
        ogroup.add_option("--static", action="store_true", default=False,
                help="Install using static options.")
        parser.add_option_group(ogroup)
        return parser

    def setup(self, options, args):
        if len(args) == 0:
            parser.error("Command 'info' requires at least one package")
        self._pkgs = args
        self.opts = options
        self._static = options.static
        #pybombs_ops.config_set("static", str(self._static))
        # FIXME This skips the case where --static is not supplied
        # on the cmd line, but is in the config settings


    def run(self):
        " Go, go, go! "

        recipe_manager = RecipeListManager()
        inv_manager = InventoryManager()
        install_tree = simple_tree.SimpleTree()

        ### Step 1: Make a list of packages to install
        # Loop through all packages to install
        for pkg in self._pkgs:
            # Check is a valid package:
            if self.recipe_manager.get_recipe(pkg) is None:
                self.log.error("Package not in recipe list: {}".format(pkg))
                exit(1)

            # Check if we already covered this package
            if pkg in install_tree.get_nodes():
                continue
            # Check if package is already installed:
            if inv_manager.get_version(pkg) is None:
                install_tree.insert_at(pkg)
                self._add_deps_recursive(install_tree, pkg)
            else:
                # TODO: Do something if we want to reinstall or update
                pass

        self.log.debug("Install tree:")
        install_tree.pretty_print()

        ### Step 2: Recursively install, starting at the leaf nodes
        while not install_tree.empty():
            pkg = install_tree.pop_leaf_node()
            self.log.debug("Installing package: {}".format(pkg))
            # Fetch (unless doing a reinstall, in that case, check source is available)
            # Install
            # Add to inventory

        #for p in self._pkgs:
            #self.run_install(p)


    def _add_deps_recursive(self, install_tree, pkg):
        """
        Recursively add dependencies to the install tree.
        """
        recipe = self.recipe_manager.get_recipe(pkg)
        deps = recipe.get_deps()
        deps_to_install = [dep for dep in deps if not dep in install.get_nodes()]
        if len(deps_to_install) == 0:
            return
        install_tree.insert_at(deps_to_install, pkg)
        for dep in deps_to_install:
            self._add_deps_recursive(install_tree, dep)



    def run_install(self, pkgname):
        """
        Install the package called pkgname.

        Order of ops for each pkgname:
        - Check if pkgname is in the recipe list
        - Ask for a Recipe object and see if it's already installed
          - If yes, figure out if we want to reinstall
            - If no, return
        - Ask the RecipeListManager for a list of dependencies (recursively)
        - For every dependency, ask Recipe if it's already installed in
          the current prefix
        - Create a new list of all Recipes that need to be installed
        - Install each of these
        """
        self.log.info("Starting installation of package {0}".format(pkgname))


        if not check_recipe(pkgname):
            die("unknown package "+pkgname);
        if die_if_already and check_installed(pkgname):
            print pkgname + " already installed";
            return;
        validate_write_perm(vars["prefix"])
        rc = global_recipes[pkgname];
        pkg_missing = rc.recursive_satisfy();

        # remove duplicates while preserving list order (lowest nodes first)
        pkg_missing = list_unique_ord(pkg_missing);
        self.log.info("Installing packages:\n" + "\n".join(["* {0}".format(x) for x in pkg_missing]))

        # prompt if list is ok?
        # provide choice of deb satisfiers or source build?

        for pkg in pkg_missing:
            global_recipes[pkg].install();
            if(pkg == "gnuradio"):
                if(confirm("Run VOLK Profile to choose fastest kernels?","Y",5)):
                    run_volk_profile();
    #    global_recipes[pkgname].install();

