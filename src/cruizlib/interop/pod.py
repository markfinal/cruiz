"""Plain old data utilities for interop between Conan and UI."""

from __future__ import annotations

import pathlib
from dataclasses import dataclass

from attrs.converters import to_bool


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
        enabled = to_bool(enabled_arg)
        return cls(path, enabled)
