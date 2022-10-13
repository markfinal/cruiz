#!/usr/bin/env python3

"""
Enumeration for each binary type
"""

from enum import IntFlag
from enum import auto


class ConanPackageTypeFlags(IntFlag):
    """
    Flags for each binary type of Conan package
    """

    BUILDABLE = auto()
    BINARY = auto()
    EDITABLE = auto()
