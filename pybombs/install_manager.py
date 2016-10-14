#
# Copyright 2016 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
#
# GNU Radio is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# GNU Radio is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GNU Radio; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#
""" Handles installing multiple packets """

from __future__ import print_function
from pybombs import pb_logging
from pybombs import package_manager
from pybombs import dep_manager

class InstallManager(object):
    """
    Handles installing packages.
    """
    def __init__(self):
        self.pm = package_manager.PackageManager()
        self.log = pb_logging.logger.getChild("install_manager")

    def install(
            self,
            packages,
            mode, # install / update
            fail_if_not_exists=False, # Fail if any package in `packages' is not already installed
            update_if_exists=False,
            quiet=False,
            print_tree=False,
            deps_only=False,
            no_deps=False,
            verify=False,
            static=False,
            install_type=None
        ):
        """
        Install packages.
        """
        def _check_if_pkg_goes_into_tree(pkg):
            " Return True if pkg has a legitimate right to be in the tree. "
            if fail_if_not_exists:
                return bool(self.pm.installed(pkg))
            if no_deps and pkg not in packages:
                return False
            if not self.pm.installed(pkg):
                # If it's not installed, we'll try a binary install...
                self.log.debug("Testing binary install for package {pkg}.".format(pkg=pkg))
                if self.pm.install(pkg, install_type="binary",
                                   static=static, verify=verify,
                                   fail_silently=True):
                    # ...and if that worked, it doesn't have to go into the tree.
                    return False
                # Now it's still not installed, so it has to go into the tree:
                return True
            else:
                # If a package is already installed, but not flagged for
                # updating, it does not go into the tree:
                if not update_if_exists or not pkg in packages:
                    return False
                # OK, so it needs updating. But only if it's a source package:
                if self.pm.installed(pkg, install_type="source"):
                    return True
                # Otherwise, we should give it a shot:
                self.pm.update(pkg, install_type="binary")
            assert False # Should never reach this line
        ####### install() starts here #########
        ### Sanity checks
        if fail_if_not_exists:
            for pkg in packages:
                if not self.pm.installed(pkg):
                    self.log.error("Package {0} is not installed. Aborting.".format(pkg))
                    return False
        extra_info_logger = self.log.info if not quiet else self.log.debug
        ### Make install tree and install binary packages
        extra_info_logger("Phase 1: Creating install tree and installing binary packages:")
        install_tree = dep_manager.DepManager(self.pm).make_dep_tree(
            packages,
            _check_if_pkg_goes_into_tree
        )
        if len(install_tree) == 0 and not quiet:
            self.log.info("No packages to install.")
            return True
        if (self.log.getEffectiveLevel() <= 20 or print_tree) and not quiet:
            print("Install tree:")
            install_tree.pretty_print()
        if len(install_tree) > 0 and install_type == "binary":
            self.log.error("Install method was `binary', but source packages are left over!")
            return False
        ### Recursively install/update source packages, starting at the leaf nodes
        extra_info_logger("Phase 2: Recursively installing source packages to prefix:")
        for pkg in install_tree.serialize():
            if mode == 'install' and deps_only and pkg in packages:
                self.log.debug("Skipping `{0}' because only deps are requested.")
                continue
            if self.pm.installed(pkg):
                self.log.info("Updating package: {0}".format(pkg))
                if not self.pm.update(pkg, verify=verify):
                    self.log.error("Error updating package {0}. Aborting.".format(pkg))
                    return False
                self.log.info("Update successful.")
            else:
                self.log.info("Installing package: {0}".format(pkg))
                if not self.pm.install(pkg, static=static, verify=verify):
                    self.log.error("Error installing package {0}. Aborting.".format(pkg))
                    return False
                self.log.info("Installation successful.")
        return True

