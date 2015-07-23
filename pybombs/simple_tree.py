#!/usr/bin/env python2
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
Simple Tree object, mainly for dependency tracking
"""

class SimpleTree(object):
    """
    Very simple tree object. Stored as a list of lists.
    Anything not a list is considered a data node.
    Example: ['a', ['aa', 'ab'], 'b', ['ba', 'bb', ['bba', 'bbb']]]
    Beneath the root, there are two nodes, a and b. a has two subnodes,
    aa and ab. b has two subnodes, of which the second one, bb, also has
    subnodes.
    """
    def __init__(self):
        self._tree = []

    def is_node(self, node):
        """
        Returns true if node contains data (== is not a subtree)
        """
        return not isinstance(node, list)

    def is_subtree(self, node):
        """
        Returns true if node is a subtree (== does not contain data)
        """
        return isinstance(node, list)

    def empty(self):
        """
        Returns True if there are no nodes in the tree.
        """
        self.prune()
        return len(self._tree) == 0

    def pop_leaf_node(self, subtree=None):
        """
        Pops any leaf node and returns its value.
        """
        if subtree is None:
            if self.empty():
                return None
            return self.pop_leaf_node(self._tree)
        self.prune(subtree)
        for node in subtree:
            if self.is_subtree(node):
                return self.pop_leaf_node(node)
        # No more subtrees available, so return any leaf node:
        leaf_node = subtree[0]
        subtree.remove(leaf_node)
        return leaf_node

    def prune(self, node=None):
        """
        Remove empty list objects from this tree.
        """
        if node is None:
            if len(self._tree) == 0:
                return
            return self.prune(self._tree)
        for sub_node in node:
            if self.is_subtree(sub_node):
                self.prune(sub_node)
        while [] in node:
            node.remove([])

    def insert_at(self, subtree, target_node=None, root=None):
        """
        Inserts a subtree under target_node.
        If target_node is None, the node gets inserted into
        the root. Otherwise, if target_node doesn't exist, return
        False and do not insert subtree.
        """
        if target_node is None:
            self._tree.append(subtree)
            return True
        if root is None:
            return self.insert_at(subtree, target_node, self._tree)
        if target_node in root:
            root.insert(root.index(target_node) + 1, subtree)
            return True
        else:
            for node in root:
                if self.is_subtree(node):
                    if self.insert_at(subtree, target_node, node):
                        return True
            return False

    def get_nodes(self, root_node=None, node_list=[]):
        """
        Return all data nodes as an unordered list
        """
        if root_node is None:
            root_node = self._tree
        for node in root_node:
            if self.is_node(node):
                node_list.append(node)
            else:
                node_list = self.get_nodes(node, node_list)
        return node_list


    def pretty_print(self, indent='', root_node=None):
        """
        Pretty-prints the tree to the console.
        """
        if root_node is None:
            self.prune()
            root_node = self._tree
        # This is true after we print an actual data node:
        printed_node = False
        lead_char = '|'
        for idx, node in enumerate(root_node):
            if idx == len(root_node) - 1:
                lead_char = ' '
            if self.is_node(node):
                print indent + '|'
                print "{0}{1}- {2}".format(indent, '\\' if  idx == len(root_node) - 1 else '+', str(node))
                printed_node = True
            else:
                if not printed_node:
                    print indent + '+--\\'
                self.pretty_print(indent + lead_char + "  ", node)
                printed_node = False


if __name__ == "__main__":
    tree = SimpleTree()
    print "Testing pretty_print():"
    tree._tree = ['root', 'root2', [ ['foo', 'bar'] ], [ ['baz', 'fee'] ],]
    tree.pretty_print()
    print "Testing get_nodes():"
    print tree.get_nodes()
    print "\nTesting pop_leaf_node():"
    while not tree.empty():
        print tree.pop_leaf_node()
    tree.pretty_print()
    print "\nTesting prune():"
    tree._tree = [ [ ['foo', 'bar', []] ], [ [[], 'baz', 'fee', []], [] ], [], ]
    tree.prune()
    tree.pretty_print()
    print "\nTesting insert_at():"
    tree.insert_at(["dep1", "dep2"], 'foo')
    tree.insert_at(None, 'new_root_node')
    tree.pretty_print()

