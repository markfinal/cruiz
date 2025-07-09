#!/usr/bin/env python3

"""
Global non-GUI variables.

(could do without these)
"""

CONAN_FULL_VERSION: str = "undetermined"
CONAN_MAJOR_VERSION: int = 0  # pylint: disable=invalid-name


def __capture_conan_version() -> None:
    global CONAN_FULL_VERSION, CONAN_MAJOR_VERSION  # pylint: disable=global-statement

    import importlib.metadata  # pylint: disable=import-outside-toplevel

    CONAN_FULL_VERSION = importlib.metadata.version("conan")

    version_components = CONAN_FULL_VERSION.split(".")
    CONAN_MAJOR_VERSION = int(version_components[0])


__capture_conan_version()
