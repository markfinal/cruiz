"""Tests for DependencyGraph."""

from cruizlib.interop.dependencygraph import dependencygraph_from_node_dependees
from cruizlib.interop.packagenode import PackageNode


def test_dependencygraph() -> None:
    """
    Test manipulating a dependency graph.

    The reason the number of nodes tested is 2 instead of 3 is because
    the function does not recursively walk the dependency graph.
    """
    NON_RECURSIVE_NODE_DEPTH = 2

    pkgA = PackageNode(
        "PkgA", "PkgA/1.0", "1234", "ABCD", True, "InfoA", True, "LayoutA"
    )
    pkgB = PackageNode(
        "PkgB", "PkgB/2.0", "5678", "EFGH", True, "InfoB", True, "LayoutB"
    )
    pkgC = PackageNode(
        "PkgC", "PkgC/3.0", "91011", "IJKL", True, "InfoC", True, "LayoutC"
    )

    # C depends on B depends on A
    pkgC.children = [pkgB]
    pkgB.parents = [pkgC]
    pkgB.children = [pkgA]
    pkgA.parents = [pkgB]

    inverted = dependencygraph_from_node_dependees(pkgA)
    assert len(inverted.nodes) == NON_RECURSIVE_NODE_DEPTH
