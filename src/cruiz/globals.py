#!/usr/bin/env python3

"""
Global variables
(could do without these)
"""

from __future__ import annotations
import typing

CRUIZ_MAINWINDOW: typing.Optional[cruiz.MainWindow] = None  # type: ignore # noqa: F821

CONAN_FULL_VERSION: str = "undetermined"
CONAN_MAJOR_VERSION: int = 0

CRUIZ_THEME: typing.Optional[str] = None


def get_main_window() -> cruiz.MainWindow:  # type: ignore # noqa: F821
    """
    Get the main window for the application, asserting it is valid
    """
    assert CRUIZ_MAINWINDOW
    return CRUIZ_MAINWINDOW


def get_theme() -> str:
    """
    Get the name of the current theme
    """
    assert CRUIZ_THEME
    return CRUIZ_THEME


def is_dark_theme() -> bool:
    """
    Is the current theme the dark theme?
    """
    assert CRUIZ_THEME
    return CRUIZ_THEME == "Dark"


def __capture_conan_version() -> None:
    global CONAN_MAJOR_VERSION
    if CONAN_MAJOR_VERSION > 0:
        return

    import importlib.metadata

    global CONAN_FULL_VERSION
    CONAN_FULL_VERSION = importlib.metadata.version("conan")
    version_components = CONAN_FULL_VERSION.split(".")
    CONAN_MAJOR_VERSION = int(version_components[0])


__capture_conan_version()
