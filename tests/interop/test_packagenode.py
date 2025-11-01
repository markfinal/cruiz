"""Tests for PackageNode."""

import dataclasses

from cruizlib.interop.packagenode import PackageNode


def test_packagenode() -> None:
    """Test manipulating packagenodes."""
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

    # get all the fields of the PackageNode of interest to check
    fields = dataclasses.fields(pkg_a)
    fields = tuple(
        field for field in fields if field.name not in ("children", "parents")
    )

    pkg_a_s = pkg_a.clone_standalone()
    for field in fields:
        assert getattr(pkg_a_s, field.name) == getattr(pkg_a, field.name)
    assert isinstance(pkg_a_s.parents, list) and not pkg_a_s.parents
    assert isinstance(pkg_a_s.children, list) and not pkg_a_s.children

    pkg_b_s = pkg_b.clone_standalone()
    for field in fields:
        assert getattr(pkg_b_s, field.name) == getattr(pkg_b, field.name)
    assert isinstance(pkg_b_s.parents, list) and not pkg_b_s.parents
    assert isinstance(pkg_b_s.children, list) and not pkg_b_s.children

    pkg_c_s = pkg_c.clone_standalone()
    for field in fields:
        assert getattr(pkg_c_s, field.name) == getattr(pkg_c, field.name)
    assert isinstance(pkg_c_s.parents, list) and not pkg_c_s.parents
    assert isinstance(pkg_c_s.children, list) and not pkg_c_s.children
