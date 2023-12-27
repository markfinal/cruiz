#!/usr/bin/env python3

"""
Interop between Conan and cruiz
"""

from __future__ import annotations

from dataclasses import dataclass, field
import typing


@dataclass
class PackageNode:
    """
    Representation of a node in the Conan dependency graph
    """

    name: str
    reference: str
    package_id: str
    recipe_revision: str
    short_paths: bool
    info: typing.Optional[str]
    is_runtime: bool
    layout_build_subdir: str
    children: typing.List[PackageNode] = field(default_factory=list)
    parents: typing.List[PackageNode] = field(default_factory=list)

    def clone_standalone(self) -> PackageNode:
        return PackageNode(
            self.name,
            self.reference,
            self.package_id,
            self.recipe_revision,
            self.short_paths,
            self.info,
            self.is_runtime,
            self.layout_build_subdir,
            [],
            [],
        )
