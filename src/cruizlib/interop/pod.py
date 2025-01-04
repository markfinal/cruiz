"""Plain old data utilities for interop between Conan and UI."""

from __future__ import annotations

import pathlib
from dataclasses import dataclass


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
class ConanHook:
    """Plain old data class representing a Conan hook."""

    path: pathlib.Path
    enabled: bool

    def has_path(self, path: pathlib.Path) -> bool:
        """Return whether the hook contains the specified path."""
        return self.path in (path, path.stem)

    @classmethod
    def from_string(cls, string: str) -> ConanHook:
        """Convert a string to a ConanHook."""
        assert string.startswith("ConanHook(")
        assert string.endswith(")")
        string = string.replace("ConanHook(", "")
        string = string.rstrip(")")
        args = string.split(",")
        assert len(args) == 2
        # two args, path=ClassName('/path/to'), enabled=True|False
        path_arg = args[0].strip().replace("path=", "")
        path_start = path_arg.find("(") + 1
        path_end = path_arg.find(")")
        path_arg = path_arg[path_start:path_end][1:-1]
        path = pathlib.Path(path_arg)
        enabled_arg = args[1].strip().replace("enabled=", "")
        enabled = _strtobool(enabled_arg)
        return cls(path, enabled)
