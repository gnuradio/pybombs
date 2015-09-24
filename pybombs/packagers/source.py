#
# Copyright 2015 Free Software Foundation, Inc.
#
# This file is part of PyBOMBS
#
# PyBOMBS is free software you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation either version 3, or (at your option)
# any later version.
#
# PyBOMBS is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyBOMBS see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#
"""
Packager: Source packages
"""

import os
import re
import copy
import shutil
from pybombs import pb_logging
from pybombs import inventory
from pybombs.utils import subproc
from pybombs.utils import output_proc
from pybombs.pb_exception import PBException
from pybombs.fetcher import Fetcher
from pybombs.config_manager import config_manager
from pybombs.packagers.base import PackagerBase


class Source(PackagerBase):
    name = "source"

    """
    Source package manager.
    """
    def __init__(self):
        PackagerBase.__init__(self)
        if self.cfg.get_active_prefix().prefix_dir is None:
            self.log.error("No prefix specified. Aborting.")
            exit(1)
        self.prefix = self.cfg.get_active_prefix()
        self.inventory = inventory.Inventory(self.prefix.inv_file)
        self.static = False

    def supported(self):
        """
        We can always build source packages.
        """
        return True

    def exists(self, recipe):
        """
        This will work whenever any sources are defined.
        """
        if not hasattr(recipe, 'source') or len(recipe.source) == 0:
            return None
        # Return a pseudo-version
        # TODO check if we can get something better from the inventory
        return "0.0"

    def install(self, recipe, static=False):
        """
        Run the source installation process for package 'recipe'.

        May raise an exception if things go terribly wrong.
        Otherwise, return True on success and False if installing failed.
        """
        self.static = static
        recipe.set_static(static)
        cwd = os.getcwd()
        if not hasattr(recipe, 'source') or len(recipe.source) == 0:
            self.log.warning("Cannot find a source URI for package {}".format(recipe.id))
            return False
        try:
            initial_state = self.inventory.get_state(recipe.id)
            if initial_state is None:
                initial_state = 0
            self.log.debug("State on package {} is {}".format(recipe.id, initial_state))
            # First, make sure we have the sources
            if self.inventory.get_state(recipe.id) < self.inventory.STATE_FETCHED:
                Fetcher().fetch(recipe)
            else:
                self.log.debug("Package {} is already fetched.".format(recipe.id))
            # Set up the build dir
            pkg_src_dir = os.path.join(self.prefix.src_dir, recipe.id)
            builddir = os.path.join(pkg_src_dir, recipe.installdir)
            # The package source dir must exist, or something is wrong.
            if not os.path.isdir(pkg_src_dir):
                self.log.error("There should be a source dir in {}, but there isn't.".format(pkg_src_dir))
                return False
            if os.path.exists(os.path.join(pkg_src_dir, builddir)):
                #shutil.rmtree(builddir)
                self.log.warn("Build dir already exists: {}".format(builddir))
            else:
                os.mkdir(builddir)
            os.chdir(builddir)
            ### Run the build process
            if self.inventory.get_state(recipe.id) < self.inventory.STATE_CONFIGURED:
                self.configure(recipe)
                self.inventory.set_state(recipe.id, self.inventory.STATE_CONFIGURED)
                self.inventory.save()
            else:
                self.log.debug("Package {} is already configured.".format(recipe.id))
            if self.inventory.get_state(recipe.id) < self.inventory.STATE_BUILT:
                self.make(recipe)
                self.inventory.set_state(recipe.id, self.inventory.STATE_BUILT)
                self.inventory.save()
            else:
                self.log.debug("Package {} is already built.".format(recipe.id))
            if self.inventory.get_state(recipe.id) < self.inventory.STATE_INSTALLED:
                self.make_install(recipe)
                self.inventory.set_state(recipe.id, self.inventory.STATE_INSTALLED)
                self.inventory.save()
            else:
                self.log.debug("Package {} is already installed.".format(recipe.id))
        except PBException as err:
            os.chdir(cwd)
            self.log.error("Problem occured while building package {}:\n{}".format(recipe.id, str(err).strip()))
            return False
        ### Housekeeping
        os.chdir(cwd)
        return True

    def installed(self, recipe):
        """
        We read the version number from the inventory. It might not exist,
        but that's OK.
        """
        if self.inventory.has(recipe.id) and self.inventory.get_state(recipe.id) == 'installed':
            return self.inventory.get_version(recipe.id, True)
        return False

    #########################################################################
    # Build methods: All of these must raise a PBException when something
    # goes wrong.
    #########################################################################
    def configure(self, recipe, try_again=False):
        """
        Run the configuration step for this recipe.
        If try_again is set, it will assume the configuration failed before
        and we're trying to run it again.
        """
        self.log.debug("Configuring recipe {}".format(recipe.id))
        self.log.debug("Using vars - {}".format(recipe.vars))
        self.log.debug("In cwd - {}".format(os.getcwd()))
        pre_cmd = recipe.var_replace_all(recipe.get_command('configure'))
        cmd = self.filter_cmd(pre_cmd, recipe, 'config_filter')
        o_proc = None
        if self.log.getEffectiveLevel() >= pb_logging.DEBUG and not try_again:
            o_proc = output_proc.OutputProcessorMake(preamble="Configuring: ")
        if subproc.monitor_process(cmd, shell=True, o_proc=o_proc) == 0:
            self.log.debug("Configure successful.")
            return True
        # OK, something went wrong.
        if try_again == False:
            self.log.warning("Configuration failed. Re-trying with higher verbosity.")
            return self.configure(recipe, try_again=True)
        else:
            self.log.error("Configuration failed after running at least twice.")
            raise PBException("Configuration failed")

    def make(self, recipe, try_again=False):
        """
        Build this recipe.
        If try_again is set, it will assume the build failed before
        and we're trying to run it again. In this case, reduce the
        makewidth to 1 and show the build output.
        """
        self.log.debug("Building recipe {}".format(recipe.id))
        self.log.debug("In cwd - {}".format(os.getcwd()))
        o_proc = None
        if self.log.getEffectiveLevel() >= pb_logging.DEBUG and not try_again:
            o_proc = output_proc.OutputProcessorMake(preamble="Building: ")
        cmd = recipe.var_replace_all(recipe.get_command('make'))
        cmd = self.filter_cmd(cmd, recipe, 'make_filter')
        if subproc.monitor_process(cmd, shell=True, o_proc=o_proc) == 0:
            self.log.debug("Make successful")
            return True
        # OK, something bad happened.
        if try_again == False:
            recipe.vars['makewidth'] = '1'
            self.make(recipe, try_again=True)
        else:
            self.log.error("Build failed. See output above for error messages.")
            raise PBException("Build failed.")

    def make_install(self, recipe):
        """
        Run 'make install' or whatever copies the files to the right place.
        """
        self.log.debug("Installing package {}".format(recipe.id))
        self.log.debug("In cwd - {}".format(os.getcwd()))
        pre_cmd = recipe.var_replace_all(recipe.get_command('install'))
        cmd = self.filter_cmd(pre_cmd, recipe, 'install_filter')
        o_proc = None
        if self.log.getEffectiveLevel() >= pb_logging.DEBUG:
            o_proc = output_proc.OutputProcessorMake(preamble="Installing: ")
        if subproc.monitor_process(cmd, shell=True, o_proc=o_proc) == 0:
            self.log.debug("Installation successful")
            return True
        raise PBException("Installation failed")

    #########################################################################
    # Helpers
    #########################################################################
    def filter_cmd(self, unfiltered_command, recipe, filter_flag):
        """
        - Get a filter from the recipe flags identified by filter_flag
        - If filter is empty, return unfiltered_command verbatim
        - Replace all variables in the filter
            - $command is replaced by unfiltered_command
        """
        cmd_filter = self.cfg.get_package_flags(recipe.id, recipe.category).get(filter_flag)
        if not cmd_filter:
            return unfiltered_command
        self.log.obnoxious('Filtering command using: {filt}'.format(filt=cmd_filter))
        recipe.vars['command'] = unfiltered_command
        return recipe.var_replace_all(cmd_filter)

