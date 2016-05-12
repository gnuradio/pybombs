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

from pybombs.tree_node import TreeNode
from pybombs import package_manager
from pybombs import config_manager
from pybombs import pb_logging
from pybombs import recipe
from pybombs.pb_exception import PBException

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
        # - all of pkg_list goes into a set P
        # - init an empty dict D
        # - for every element p of P:
        #   - create a full dep tree T
        #   - D[p] -> T
        #   - for every element q of P\p:
        #     - if q is in T, then P <- P\q and del(D[q]) if exists
        # - merge all elements of D into T' and return that
        pkg_set = set(filter(filter_callback, pkg_list))
        new_pkg_set = set(filter(filter_callback, pkg_list))
        dep_trees = {}
        for pkg in pkg_set:
            dep_trees[pkg] = self.make_tree_recursive(pkg, filter_callback)
            assert dep_trees[pkg] is not None
            for other_pkg in new_pkg_set.difference([pkg]):
                if other_pkg in dep_trees[pkg]:
                    new_pkg_set.remove(other_pkg)
        install_tree = TreeNode()
        for pkg in new_pkg_set:
            install_tree.add_child(dep_trees[pkg])
        return install_tree

    def make_tree_recursive(self, pkg, filter_callback):
        """
        Make a dependency tree for one package
        """
        if not filter_callback(pkg):
            return None
        tree = TreeNode(pkg)
        deps = recipe.get_recipe(pkg).depends or []
        for dep in deps:
            if not self.pm.exists(pkg):
                raise PBException(
                    "Package does not exist: {0} (declared as dependency for package {1})".format(
                        dep, pkg
                    )
                )
        deps_to_install = set([dep for dep in deps if filter_callback(dep)])
        for dep in deps_to_install:
            subtree = self.make_tree_recursive(dep, filter_callback)
            if subtree is not None:
                tree.add_child(subtree)
        return tree

