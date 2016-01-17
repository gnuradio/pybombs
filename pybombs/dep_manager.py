#
# Copyright 2015 Free Software Foundation, Inc.
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
""" PyBOMBS dependency manager """

from pybombs.simple_tree import SimpleTree
from pybombs import package_manager
from pybombs import config_manager
from pybombs import pb_logging
from pybombs import recipe

class DepManager(object):
    """
    Dependency manager.
    """
    def __init__(self):
        self.pm = package_manager.PackageManager()
        self.cfg = config_manager.config_manager
        self.log = pb_logging.logger.getChild("DepManager")

    def make_dep_tree(self, pkg_list, filter_callback):
        """
        - pkg_list: List of package names.
        - filter_callback: Function that takes a package name
          and returns True if the package should go into the tree.
        """
        install_tree = SimpleTree()
        for pkg in pkg_list:
            # Check is a valid package:
            if not self.pm.exists(pkg):
                self.log.error("Package does not exist: {}".format(pkg))
                exit(1)
            # Check if this package should even go into the tree
            if not filter_callback(pkg):
                continue
            # Check if we already covered this package
            if pkg in install_tree.get_nodes():
                continue
            install_tree.insert_at(pkg)
            self._add_deps_recursive(install_tree, pkg, filter_callback)
        return install_tree

    def _add_deps_recursive(self, install_tree, pkg, filter_callback):
        """
        Recursively add dependencies to the install tree.
        """
        # Load deps:
        deps = recipe.get_recipe(pkg).get_local_package_data()['depends'] or []
        # Filter for illegal stuff:
        for dep in deps:
            if not self.pm.exists(pkg) and dep is not None:
                self.log.error("Package does not exist: {0} (declared as dependency for package {1})".format(dep, pkg))
                exit(1)
        # Filter all packages either already in the tree, or not wanted:
        deps_to_install = filter(
            lambda pkg: filter_callback(pkg) and pkg not in install_tree.get_nodes(),
            deps
        )
        if len(deps_to_install) == 0:
            return
        # First, add all dependencies into the install tree:
        install_tree.insert_at(deps_to_install, pkg)
        # Then, extend the tree if the dependencies have dependencies themselves:
        for dep in deps_to_install:
            if isinstance(dep, list):
                # I honestly have no clue why this happens, yet sometimes
                # it does.
                continue
            self._add_deps_recursive(install_tree, dep, filter_callback)

