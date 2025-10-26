#!/usr/bin/env python3

"""
Global non-GUI variables.

(could do without these)
"""

import importlib.metadata
import typing


def __capture_conan_version() -> typing.Tuple[str, int]:
    full_version = importlib.metadata.version("conan")

    version_components = full_version.split(".")
    major_version = int(version_components[0])

    return full_version, major_version


CONAN_FULL_VERSION, CONAN_MAJOR_VERSION = __capture_conan_version()
