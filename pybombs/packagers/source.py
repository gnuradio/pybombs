#
# Copyright 2015-2016 Free Software Foundation, Inc.
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
import shutil
from pybombs import pb_logging
from pybombs.requirer import Requirer
from pybombs.utils import subproc
from pybombs.utils import output_proc
from pybombs.pb_exception import PBException
from pybombs.packagers.base import PackagerBase

class Source(PackagerBase):
    """
    Source package manager.
    """
    name = "source"
    host_sys_deps = ['build-essential',]

    def __init__(self):
        PackagerBase.__init__(self)
        if self.cfg.get_active_prefix().prefix_dir is None:
            self.log.error("No prefix specified. Aborting.")
            raise PBException("No prefix specified.")
        self.prefix = self.cfg.get_active_prefix()
        self.inventory = self.prefix.inventory
        self.static = False

    def supported(self):
        """
        We can always build source packages unless disabled in the config.
        """
        return 'src' in self.cfg.get('satisfy_order')

    def exists(self, recipe):
        """
        This will work whenever any sources are defined.
        """
        if not hasattr(recipe, 'source') or len(recipe.source) == 0:
            return None
        # Return a pseudo-version
        # TODO check if we can get something better from the inventory
        return True

    def installed(self, recipe):
        """
        We read the version number from the inventory. It might not exist,
        but that's OK.
        """
        if self.inventory.get_state(recipe.id) == self.inventory.STATE_INSTALLED:
            return self.inventory.get_version(recipe.id, True)
        return False

    def install(self, recipe, static=False, update=False):
        """
        Run the source installation process for package 'recipe'.

        May raise an exception if things go terribly wrong.
        Otherwise, return True on success and False if installing failed.
        """
        if not os.path.isdir(self.prefix.src_dir):
            os.makedirs(self.prefix.src_dir)
        self.static = static
        recipe.set_static(static)
        cwd = os.getcwd()
        get_state = lambda: (self.inventory.get_state(recipe.id) or 0)
        set_state = lambda state: self.inventory.set_state(recipe.id, state) or self.inventory.save()
        if not hasattr(recipe, 'source') or len(recipe.source) == 0:
            self.log.warn("Cannot find a source URI for package {0}".format(recipe.id))
            return False
        from pybombs.fetcher import Fetcher
        try:
            if update:
                if get_state() < self.inventory.STATE_CONFIGURED:
                    raise PBException("Can't update package {0}, it's not yet configured.".format(recipe.id))
                Fetcher().update(recipe)
                set_state(self.inventory.STATE_CONFIGURED)
            self.log.debug("State on package {0} is {1}".format(recipe.id, get_state()))
            # First, make sure we have the sources
            if not update and get_state() < self.inventory.STATE_FETCHED:
                Fetcher().fetch(recipe)
            else:
                self.log.debug("Package {} is already fetched.".format(recipe.id))
            # If we know the package is fetched, we can attempt to build:
            self.run_build(
                recipe,
                nuke_builddir=False,
                warn_if_builddir_exists=not bool(update),
                fail_if_builddir_missing=update,
            )
        except PBException as err:
            os.chdir(cwd)
            self.log.error("Problem occurred while building package {}:\n{}".format(recipe.id, str(err).strip()))
            return False
        ### Housekeeping
        os.chdir(cwd)
        return True

    def update(self, recipe):
        """
        Update the source package. Algorithm:
        - Check it's at least in state 'configured'
        - Do a fetch-update
        - Set state to 'fetched' if it was not configured, and 'configured'
          otherwise
        - Jump straight to 'make' step
        - Continue like install()

        This is actually handled by the install() function.
        """
        return self.install(recipe, update=True)

    def uninstall(self, recipe):
        """
        Remove a source-installed installation.
        """
        cwd = os.getcwd()
        pkg_src_dir = os.path.normpath(os.path.join(self.prefix.src_dir, recipe.id))
        builddir = os.path.normpath(os.path.join(pkg_src_dir, recipe.installdir))
        get_state = lambda: (self.inventory.get_state(recipe.id) or 0)
        set_state = lambda state: self.inventory.set_state(recipe.id, state) or self.inventory.save()
        if not os.path.isdir(pkg_src_dir):
            set_state(0)
            raise PBException("There should be a source dir in {0}, but there isn't.".format(pkg_src_dir))
        if get_state() >= self.inventory.STATE_INSTALLED:
            self.log.debug("Using build directory: {0}".format(builddir))
            if not os.path.isdir(builddir):
                self.log.warn("Package claims to be installed, but no build dir. Cannot do a proper uninstall.")
            else:
                try:
                    os.chdir(builddir)
                    self.make_clean(recipe)
                    os.chdir(cwd)
                except PBException as ex:
                    self.log.warn("Uninstall failed: {0}.".format(str(ex)))
                    return False
            set_state(self.inventory.STATE_CONFIGURED)
        if get_state() >= self.inventory.STATE_FETCHED:
            self.log.debug("Removing directory {0}.".format(pkg_src_dir))
            shutil.rmtree(pkg_src_dir)
            self.inventory.remove(recipe.id)
            self.inventory.save()
        self.log.obnoxious("Uninstall complete.")
        return True

    def rebuild(self, recipe, make_clean=False, nuke_builddir=False):
        """
        - Reset the state to 'fetched'
        - Trigger run_build
        """
        self.inventory.set_state(recipe.id, self.inventory.STATE_FETCHED)
        cwd = os.getcwd() # run_build() will change the directory
        try:
            self.run_build(
                recipe,
                make_clean=make_clean,
                nuke_builddir=nuke_builddir,
            )
            os.chdir(cwd)
            return True
        except PBException as err:
            self.log.error("Problem occurred while building package {0}:".format(recipe.id))
            self.log.error(str(err).strip())
        os.chdir(cwd)
        return False

    def run_build(self,
            recipe,
            make_clean=False,
            nuke_builddir=False,
            warn_if_builddir_exists=False,
            fail_if_builddir_missing=False,
        ):
        """
        Goes through the actual steps of configuring, building and installing
        a source package.

        Assumes source dir is in place (fetch was successful).

        Does not return a value, only raises PBException if something goes
        wrong ("net g'meckert isch lob genug").
        """
        Requirer().assert_requirements(['build-essential'])
        if nuke_builddir:
            make_clean = False
        get_state = lambda: (self.inventory.get_state(recipe.id) or 0)
        set_state = lambda state: self.inventory.set_state(recipe.id, state) or self.inventory.save()
        # Set up the build dir
        pkg_src_dir = os.path.normpath(os.path.join(self.prefix.src_dir, recipe.id))
        builddir = os.path.normpath(os.path.join(pkg_src_dir, recipe.installdir))
        self.log.debug("Using build directory: {0}".format(builddir))
        # The package source dir must exist, or something is wrong.
        if not os.path.isdir(pkg_src_dir):
            set_state(0)
            raise PBException("There should be a source dir in {0}, but there isn't.".format(pkg_src_dir))
        if builddir == pkg_src_dir:
            if nuke_builddir:
                # We can't nuke the build dir for in-tree builds, so fall back
                # to make clean:
                nuke_builddir = False
                make_clean = True
        else: # If the build dir is separate:
            if os.path.exists(builddir):
                if nuke_builddir:
                    self.log.info("Removing old build directory.")
                    shutil.rmtree(builddir)
                    os.mkdir(builddir)
                elif warn_if_builddir_exists:
                    self.log.warn("Build dir already exists: {}".format(builddir))
            else:
                if fail_if_builddir_missing:
                    raise PBException("Can't update package {0}, build directory seems to be missing.".format(recipe.id))
                os.mkdir(builddir)
        os.chdir(builddir)
        recipe.vars['builddir'] = builddir
        ### Run the build process
        if get_state() < self.inventory.STATE_CONFIGURED:
            self.configure(recipe)
            set_state(self.inventory.STATE_CONFIGURED)
        else:
            self.log.debug("Package {} is already configured.".format(recipe.id))
        if get_state() < self.inventory.STATE_BUILT:
            if make_clean:
                self.make_clean(recipe)
            self.make(recipe)
            set_state(self.inventory.STATE_BUILT)
        else:
            self.log.debug("Package {} is already built.".format(recipe.id))
        if get_state() < self.inventory.STATE_INSTALLED:
            self.make_install(recipe)
            set_state(self.inventory.STATE_INSTALLED)
        else:
            self.log.debug("Package {} is already installed.".format(recipe.id))

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
        pre_cmd = recipe.var_replace_all(self.get_command('configure', recipe))
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

    def make_clean(self, recipe, try_again=False):
        """
        Run 'make clean' or whatever clears a build before recompiling
        """
        self.log.debug("Uninstalling from recipe {}".format(recipe.id))
        self.log.debug("In cwd - {}".format(os.getcwd()))
        o_proc = None
        if self.log.getEffectiveLevel() >= pb_logging.DEBUG and not try_again:
            o_proc = output_proc.OutputProcessorMake(preamble="Uninstalling: ")
        cmd = recipe.var_replace_all(self.get_command('uninstall', recipe))
        cmd = self.filter_cmd(cmd, recipe, 'uninstall_filter')
        if subproc.monitor_process(cmd, shell=True, o_proc=o_proc) == 0:
            self.log.debug("Uninstall successful")
            return True
        # OK, something bad happened.
        if try_again == False:
            recipe.vars['makewidth'] = '1'
            self.make_clean(recipe, try_again=True)
        else:
            self.log.error("Uninstall failed. See output above for error messages.")
            raise PBException("Uninstall failed.")

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
        if self.log.getEffectiveLevel() >= pb_logging.DEBUG and not try_again and not recipe.make_interactive:
            o_proc = output_proc.OutputProcessorMake(preamble="Building:    ")
        cmd = recipe.var_replace_all(self.get_command('make', recipe))
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

    def verify(self, recipe, try_again=False):
        """
        Run 'make test' or whatever checks a build was successful
        """
        self.log.debug("Verifying package {}".format(recipe.id))
        self.log.debug("In cwd - {}".format(os.getcwd()))
        o_proc = None
        if self.log.getEffectiveLevel() >= pb_logging.DEBUG and not try_again:
            o_proc = output_proc.OutputProcessorMake(preamble="Verifying: ")
        cmd = recipe.var_replace_all(self.get_command('verify', recipe))
        cmd = self.filter_cmd(cmd, recipe, 'make_filter')
        if subproc.monitor_process(cmd, shell=True, o_proc=o_proc) == 0:
            self.log.debug("Verification successful")
            return True
        # OK, something bad happened.
        if try_again == False:
            self.log.warning("Verification failed. Retrying...")
            recipe.vars['makewidth'] = '1'
            self.verify(recipe, try_again=True)
        else:
            self.log.error("Verification failed. See output above for error messages.")
            raise PBException("Verification failed.")

    def make_install(self, recipe):
        """
        Run 'make install' or whatever copies the files to the right place.
        """
        self.log.debug("Installing package {}".format(recipe.id))
        self.log.debug("In cwd - {}".format(os.getcwd()))
        pre_cmd = recipe.var_replace_all(self.get_command('install', recipe))
        cmd = self.filter_cmd(pre_cmd, recipe, 'install_filter')
        o_proc = None
        if self.log.getEffectiveLevel() >= pb_logging.DEBUG:
            o_proc = output_proc.OutputProcessorMake(preamble="Installing:  ")
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

    def get_command(self, cmd_idx, recipe):
        """
        Look up the command for 'cmd_idx'. Consider package + category flags first,
        then recipe data.
        """
        cmd = None
        if self.static:
            cmd = self.cfg.get_package_flags(recipe.id, recipe.category).get("{cmd}_static".format(cmd=cmd_idx))
        else:
            cmd = self.cfg.get_package_flags(recipe.id, recipe.category).get(cmd_idx)
        if cmd is not None:
            return cmd
        return recipe.get_command(cmd_idx)
