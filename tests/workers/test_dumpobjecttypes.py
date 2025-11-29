"""Test that dumping object types works."""

from __future__ import annotations

import typing

from cruizlib.dumpobjecttypes import dump_object_types

if typing.TYPE_CHECKING:
    import pytest


def test_dump_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test checking None."""
    dump_object_types(None)
    monkeypatch.setenv("CRUIZ_DUMP_OBJECT_TYPES_DETAIL", "1")
    dump_object_types(None)


def test_dump_repeated_objects() -> None:
    """Test the caching of repeated objects."""
    a = 1
    b = [a, a]
    dump_object_types(b)


def test_dump_bool() -> None:
    """Test evaluating a bool."""
    dump_object_types(True)


def test_dump_dict() -> None:
    """Test evaluating a dict."""
    a = 1
    b = 2
    d = {a: b}
    dump_object_types(d)


def test_dump_object() -> None:
    """Test evaluating an object."""
    dump_object_types(None)

    # pylint: disable=too-few-public-methods
    class _ClassA:
        def __init__(self) -> None:
            self.a = 1

    # pylint: disable=too-few-public-methods
    class _ClassB:
        def __init__(self) -> None:
            self.a = _ClassA()

    b = _ClassB()
    dump_object_types(b)
