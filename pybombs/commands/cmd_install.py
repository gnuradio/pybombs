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
#import pybombs_ops as pybombs_ops

class PyBombsInstall(PyBombsCmd):
    """ Install a package """
    name = 'install'

    def __init__(self):
        PyBombsCmd.__init__(self, load_recipes=True)

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
        pass
        #for p in self._pkgs:
            #self.run_install(p)

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

