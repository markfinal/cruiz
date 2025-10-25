"""Tests for PackageNode."""

import dataclasses

from cruizlib.interop.packagenode import PackageNode


def test_packagenode() -> None:
    """Test manipulating packagenodes."""
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

    # get all the fields of the PackageNode of interest to check
    fields = dataclasses.fields(pkgA)
    fields = tuple(
        field for field in fields if field.name not in ("children", "parents")
    )

    pkgA_s = pkgA.clone_standalone()
    for field in fields:
        assert getattr(pkgA_s, field.name) == getattr(pkgA, field.name)
    assert isinstance(pkgA_s.parents, list) and not pkgA_s.parents
    assert isinstance(pkgA_s.children, list) and not pkgA_s.children

    pkgB_s = pkgB.clone_standalone()
    for field in fields:
        assert getattr(pkgB_s, field.name) == getattr(pkgB, field.name)
    assert isinstance(pkgB_s.parents, list) and not pkgB_s.parents
    assert isinstance(pkgB_s.children, list) and not pkgB_s.children

    pkgC_s = pkgC.clone_standalone()
    for field in fields:
        assert getattr(pkgC_s, field.name) == getattr(pkgC, field.name)
    assert isinstance(pkgC_s.parents, list) and not pkgC_s.parents
    assert isinstance(pkgC_s.children, list) and not pkgC_s.children
