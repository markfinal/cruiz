#!/usr/bin/env python3

"""
Global variables
(could do without these)
"""

from __future__ import annotations
import typing

CRUIZ_MAINWINDOW: typing.Optional[cruiz.MainWindow] = None  # type: ignore # noqa: F821

CONAN_MAJOR_VERSION: int = 0


def get_main_window() -> cruiz.MainWindow:  # type: ignore # noqa: F821
    """
    Get the main window for the application, asserting it is valid
    """
    assert CRUIZ_MAINWINDOW
    return CRUIZ_MAINWINDOW


def __capture_conan_version() -> None:
    global CONAN_MAJOR_VERSION
    if CONAN_MAJOR_VERSION > 0:
        return

    import subprocess

    get_conan_version = subprocess.run(
        ["conan", "--version"], capture_output=True, encoding="utf8", errors="ignore"
    )
    version = get_conan_version.stdout.replace("Conan version ", "").strip()
    if not version:
        raise ValueError("Unable to determine Conan version")
    version_components = version.split(".")
    CONAN_MAJOR_VERSION = int(version_components[0])


__capture_conan_version()
