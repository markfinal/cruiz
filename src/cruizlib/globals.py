#!/usr/bin/env python3

"""
Global non-GUI variables.

(could do without these)
"""

import importlib.metadata
import typing

from PySide6 import QtCore


def __capture_conan_version() -> typing.Tuple[int, typing.Tuple[int, ...]]:
    full_version = importlib.metadata.version("conan")

    version_components = tuple(map(int, full_version.split(".")))
    major_version = version_components[0]

    return (major_version, version_components)


CONAN_MAJOR_VERSION, CONAN_VERSION_COMPONENTS = __capture_conan_version()


def set_theme(theme: str) -> str:
    """Set the name of the current theme."""
    global CRUIZ_THEME  # pylint: disable=global-statement
    assert theme in (
        QtCore.Qt.ColorScheme.Unknown.name,
        QtCore.Qt.ColorScheme.Light.name,
        QtCore.Qt.ColorScheme.Dark.name,
    )
    CRUIZ_THEME = theme
    return theme


def get_theme() -> str:
    """Get the name of the current theme."""
    return CRUIZ_THEME


def is_dark_theme() -> bool:
    """Is the current theme the dark theme?."""
    return CRUIZ_THEME == "Dark"


CRUIZ_THEME = set_theme("Unknown")
