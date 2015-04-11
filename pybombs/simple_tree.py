


class SimpleTree(object):
    """
    Very simple tree object.
    """
    def __init__(self):
        self._tree = []

    def empty(self):
        """
        Returns True if there are no nodes in the tree.
        """
        return len(self._tree) == 0

    def pop_leaf_node(self, base_node=None, child_node=None):
        """
        Pops any leaf node and returns its value.
        """
        if base_node is None:
            if self.empty():
                return None
            return self.pop_leaf_node(self._tree, self._tree[0])
        if not isinstance(child_node, list):
            base_node.remove(child_node)
            return child_node
        elif isinstance(child_node, list) and len(child_node) == 0:
            base_node.remove(child_node)
            return None
        ret_val = self.pop_leaf_node(child_node, child_node[0])
        if ret_val is None and len(base_node) > 0:
            base_node.remove(child_node)
            if len(base_node) > 0:
                return self.pop_leaf_node(base_node, base_node[0])
        return ret_val

    def prune(self, node=None):
        """
        Remove empty list objects from this tree.
        """
        if node is None:
            if len(self._tree) == 0:
                return
            return self.prune(self._tree)
        while [] in node:
            node.remove([])
        for l in node:
            if isinstance(l, list):
                self.prune(l)

    def insert_at(self, target_node, subtree, root=None):
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
            return self.insert_at(target_node, subtree, self._tree)
        if target_node in root:
            root.insert(root.index(target_node) + 1, subtree)
            return True
        else:
            for l in root:
                if isinstance(l, list):
                    if self.insert_at(target_node, subtree, l):
                        return True
            return False


if __name__ == "__main__":
    tree = SimpleTree()
    print "Testing pop_leaf_node():"
    tree._tree = [ [ ['foo', 'bar'] ], [ ['baz', 'fee'] ], ]
    while not tree.empty():
        print tree.pop_leaf_node()
    print tree._tree
    print "Testing prune():"
    tree._tree = [ [ ['foo', 'bar', []] ], [ [[], 'baz', 'fee', []], [] ], [], ]
    tree.prune()
    print tree._tree
    print "Testing insert_at():"
    tree.insert_at('foo', ["dep1", "dep2"])
    tree.insert_at(None, 'new_root_node')
    print tree._tree

