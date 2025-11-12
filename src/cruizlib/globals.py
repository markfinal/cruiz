#!/usr/bin/env python3

"""
Global non-GUI variables.

(could do without these)
"""

import importlib.metadata
import typing


def __capture_conan_version() -> typing.Tuple[str, int, typing.Tuple[int, ...]]:
    full_version = importlib.metadata.version("conan")

    version_components = tuple(map(int, full_version.split(".")))
    major_version = version_components[0]

    return (full_version, major_version, version_components)


CONAN_FULL_VERSION, CONAN_MAJOR_VERSION, CONAN_VERSION_COMPONENTS = (
    __capture_conan_version()
)
