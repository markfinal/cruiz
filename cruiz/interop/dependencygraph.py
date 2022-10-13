#!/usr/bin/env python3

"""
Interop between Conan and cruiz
"""

from __future__ import annotations

from dataclasses import dataclass
import typing

from .packagenode import PackageNode


@dataclass
class DependencyGraph:
    """
    Representation of Conan's dependency graph
    """

    nodes: typing.List[PackageNode]
    root: PackageNode


def dependencygraph_from_node_dependees(node: PackageNode) -> DependencyGraph:
    """
    Generate a DependencyGraph from the immediate parents (those nodes requiring
    the node specified) as an inverted dependency graph.
    """
    new_root = node.clone_standalone()
    for parent in node.parents:
        new_root.children.append(parent.clone_standalone())
    new_graph = DependencyGraph(
        [new_root] + new_root.children,
        new_root,
    )
    return new_graph
