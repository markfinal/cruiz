"""Tests for DependencyGraph."""

from cruizlib.interop.dependencygraph import dependencygraph_from_node_dependees
from cruizlib.interop.packagenode import PackageNode

NON_RECURSIVE_NODE_DEPTH = 2


def test_dependencygraph() -> None:
    """
    Test manipulating a dependency graph.

    The reason the number of nodes tested is 2 instead of 3 is because
    the function does not recursively walk the dependency graph.
    """
    pkg_a = PackageNode(
        "PkgA", "PkgA/1.0", "1234", "ABCD", True, "InfoA", True, "LayoutA"
    )
    pkg_b = PackageNode(
        "PkgB", "PkgB/2.0", "5678", "EFGH", True, "InfoB", True, "LayoutB"
    )
    pkg_c = PackageNode(
        "PkgC", "PkgC/3.0", "91011", "IJKL", True, "InfoC", True, "LayoutC"
    )

    # C depends on B depends on A
    pkg_c.children = [pkg_b]
    pkg_b.parents = [pkg_c]
    pkg_b.children = [pkg_a]
    pkg_a.parents = [pkg_b]

    inverted = dependencygraph_from_node_dependees(pkg_a)
    assert len(inverted.nodes) == NON_RECURSIVE_NODE_DEPTH
