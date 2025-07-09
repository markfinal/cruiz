#!/usr/bin/env python3

"""
Global non-GUI variables.

(could do without these)
"""

CONAN_FULL_VERSION: str = "undetermined"
CONAN_MAJOR_VERSION: int = 0


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
