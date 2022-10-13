#!/usr/bin/env python3

"""
Useful constants
"""

from enum import Enum, auto


class BuildFeatureConstants(Enum):
    """
    Constants representing build features
    """

    CMAKEFINDDEBUGMODE = auto()
    CMAKEVERBOSEMODE = auto()
    CCACHEEXECUTABLE = auto()
    CCACHEAUTOTOOLSCONFIGARGS = auto()
    SCCACHEEXECUTABLE = auto()
    SCCACHEAUTOTOOLSCONFIGARGS = auto()
    BUILDCACHEEXECUTABLE = auto()
    BUILDCACHEAUTOTOOLSCONFIGARGS = auto()


class CompilerCacheTypes(Enum):
    """
    Compiler cache types
    """

    NONE = None
    CCACHE = "ccache"
    SCCACHE = "sccache"
    BUILDCACHE = "buildcache"


DEFAULT_CACHE_NAME = "Default"
