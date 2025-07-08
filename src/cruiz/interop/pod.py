#!/usr/bin/env python3

"""Plain old data classes."""

from __future__ import annotations

from dataclasses import dataclass

from attrs.converters import to_bool


@dataclass(frozen=True)
class ConanRemote:
    """Plain old data class representing a Conan remote."""

    name: str
    url: str
    enabled: bool

    @classmethod
    def from_string(cls, string: str) -> ConanRemote:
        """Convert a string into a ConanRemote."""
        assert string.startswith("ConanRemote(")
        assert string.endswith(")")
        string = string.replace("ConanRemote(", "")
        string = string.replace(")", "")
        args = string.split(",")
        assert len(args) == 3
        name_arg = args[0].strip().split("=")
        url_arg = args[1].strip().split("=")
        enabled_arg = args[2].strip().split("=")
        name = name_arg[1][1:-1]
        url = url_arg[1][1:-1]
        enabled = to_bool(enabled_arg[1])
        return cls(name, url, enabled)
