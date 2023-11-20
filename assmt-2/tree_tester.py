from a2_prefix_tree import SimplePrefixTree, CompressedPrefixTree


def verify_simple_tree_structure(tree: SimplePrefixTree) -> tuple[bool, str | None]:
    """Return `True` if tree is valid, otherwise `False`

    Checks to see if the tree structure is correct. We are NOT checking weights!
    """

    if tree.is_empty():
        return True, None

    queue = [tree]

    while queue:
        node = queue.pop()

        if node.is_leaf():  # Node is a leaf, we do not need to do anything else
            continue

        if not node.subtrees:  # Node is not a leaf but has no subtrees (this is bad!)
            return False, f"Internal Node({node.root}) has no subtrees"
        elif bad_subt := [i for i in node.subtrees if not (i.is_leaf() or len(i.root) == len(node.root) + 1)]:
            # Node has some subtrees that don't have a root with length + 1
            return False, f"Internal Node({node.root}) has subtrees with improper lengths: {[i.root for i in bad_subt]}"
        elif bad_subt := [i for i in node.subtrees if not (i.is_leaf() or i.root[:-1] == node.root)]:
            return False, f"Internal Node({node.root}) has subtrees with improper prefix: {[i.root for i in bad_subt]}"

        queue.extend(node.subtrees)

    return True, None


def verify_tree_weights(tree: SimplePrefixTree | CompressedPrefixTree, inpt: list[str, int]) -> tuple[bool, str | None]:
    """Returns whether or not tree weights are correct"""
    real_inpt = {}
    for i in inpt:
        if i[0] not in real_inpt:
            real_inpt[i[0]] = float(i[1])
        else:
            real_inpt[i[0]] += i[1]

    queue = [tree]

    while queue:
        node = queue.pop()

        if node.is_leaf():
            if node.weight != real_inpt[node.root]:
                return False, f"Internal Node({node.root})'s weight is wrong; expected: {real_inpt[node.root]}, got: {node.weight}"
        elif node.weight != (total := sum([i.weight for i in node.subtrees] + [0])):
            return False, f"Internal Node({node.root})'s weight is wrong; expected: {total}, got: {node.weight}"

        queue.extend(node.subtrees)

    return True, None


def main():
    t = SimplePrefixTree()
    inpt = [('trm', 9), ('fmi', 3), ('ijf', 6), ('nxu', 3), ('ddg', 2), ('mhk', 3), ('fac', 2), ('txt', 1), ('ruj', 1),
            ('ktp', 1), ('ljo', 4), ('cea', 8), ('pqx', 1), ('rxa', 3), ('qbe', 7), ('hiu', 8), ('nrx', 7), ('kcs', 4),
            ('gyk', 8), ('qig', 8), ('tab', 4), ('kaq', 8), ('bxm', 6), ('jqe', 7), ('ytf', 7), ('wrs', 6), ('xyd', 5),
            ('fax', 4), ('sdz', 4), ('mqe', 2), ('fmi', 3), ('ijf', 4), ('nxu', 9), ('ddg', 5), ('qbe', 2), ('hiu', 1),
            ('nrx', 4), ('kcs', 8)]

    for i in inpt:
        t.insert(i[0], float(i[1]), list(i[0]))

    # print(str(t))

    print(verify_simple_tree_structure(t))
    print(verify_tree_weights(t, inpt))


main()
