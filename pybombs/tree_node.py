#!/usr/bin/env python
" A simple tree object "

from __future__ import print_function
import copy
from functools import reduce

class TreeNode(object):
    """
    Represents part of a tree
    """
    def __init__(self, value=None):
        self._children = []
        self._value = value # None means root node

    def value(self):
        " Return node value "
        return self._value

    def __contains__(self, value):
        " Returns True if value is somewhere in the tree "
        if value == self.value():
            return True
        if len(self._children) == 0:
            return False
        return any(map(lambda node: value in node, self._children))

    def __len__(self):
        " Return number of nodes excluding root node"
        return len(self.get_values())

    def __str__(self):
        return "<node: {0}>".format(self.value())

    def empty(self):
        " Returns True if this node has no data and no sub-nodes "
        return self.__len__() == 0

    def add_child(self, child_node):
        " Add child to this node "
        if all([x != child_node.value() for x in self._children]):
            self._children.append(child_node)

    def insert_below(self, new_value, parent_value=None):
        " Add value new_value below the node with value parent_value "
        if parent_value == self.value():
            self.add_child(TreeNode(new_value))
            return True
        for child in self._children:
            try:
                child.insert_below(new_value, parent_value)
                return True
            except KeyError:
                pass
        raise KeyError("Can't insert below {0}, no such node".format(parent_value))

    def pop_leaf_node(self):
        """
        Remove any leaf node and return its value.
        Returns None if no more leaf nodes are available.
        """
        if len(self._children) == 0:
            return None
        any_child_node = self._children[-1]
        value = any_child_node.pop_leaf_node()
        if value is None:
            leaf_child_node = self._children.pop(-1)
            return leaf_child_node.value()
        return value

    def get_values(self):
        " Return all node values as a list "
        list_values = [] if self.value() is None else [self.value()]
        return reduce(lambda a, x: a + x.get_values(), self._children, list_values)

    def pretty_print(self, lead=''):
        " Pretty-prints the tree to stdout. "
        lead_char = '|'
        for idx, child in enumerate(self._children):
            if idx == len(self._children) - 1:
                lead_char = ' '
            print(lead + '|')
            print("{0}{1}- {2}".format(lead, '\\' if  idx == len(self._children)-1 else '+', str(child.value())))
            child.pretty_print(lead + lead_char + '  ')

    def serialize(self):
        """
        Returns the tree in serialized order, starting at the leaf nodes.
        Duplicates are removed.
        """
        serialized_tree = []
        tree_copy = copy.deepcopy(self)
        while len(tree_copy):
            leaf_node = tree_copy.pop_leaf_node()
            if not leaf_node in serialized_tree:
                serialized_tree.append(leaf_node)
        return serialized_tree


if __name__ == "__main__":
    tree = TreeNode()
    tree.insert_below('foo')
    print('foo' in tree)
    tree.insert_below('bar', 'foo')
    tree.insert_below('bam', 'bar')
    tree.insert_below('bam', 'foo')
    tree.insert_below('baz')
    print('baz' in tree)
    print('boom' in tree)
    print(tree.get_values())
    print(len(tree))
    tree.pretty_print()
    print(tree.serialize())
    print(tree.pop_leaf_node())
    print(len(tree))

