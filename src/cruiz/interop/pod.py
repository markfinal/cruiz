#!/usr/bin/env python3

"""Plain old data classes."""

from __future__ import annotations

import typing
from dataclasses import dataclass, field


# copied from distutils.url.strtobool and modified
def _strtobool(val: str) -> bool:
    """Convert a string representation of truth to true (1) or false (0).

    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return True
    if val in ("n", "no", "f", "false", "off", "0"):
        return False
    raise ValueError(f"Invalid truth value {val}")


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
        enabled = _strtobool(enabled_arg[1])
        return cls(name, url, enabled)


@dataclass(frozen=True)
class ExtraProfileDirectory:
    """Plain old data class representing an additional profile directory."""

    name: str
    directory: str
