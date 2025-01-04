#!/usr/bin/env python3

"""Plain old data classes."""

from __future__ import annotations

import typing
from dataclasses import dataclass, field

from attrs.converters import to_bool


@dataclass(frozen=True)
class LocalCacheDetails:
    """Plain old data class representing Conan local cache details."""

    home_directory: typing.Optional[str] = None
    short_home_directory: typing.Optional[str] = None
    extra_profile_directories: typing.List[ExtraProfileDirectory] = field(
        default_factory=list
    )
    environment: typing.Dict[str, str] = field(default_factory=dict)
    # TODO: the following are deprecated and will be removed in future
    v2_mode: typing.Optional[bool] = None
    use_revisions: typing.Optional[bool] = None


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


@dataclass(frozen=True)
class ExtraProfileDirectory:
    """Plain old data class representing an additional profile directory."""

    name: str
    directory: str
