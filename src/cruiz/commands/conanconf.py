#!/usr/bin/env python3

"""
Conan config entries of interest
"""

from enum import Enum


class ConanConfigBoolean(Enum):
    """
    Enumeration for Conan configuration items that are Boolean values

    Note that these appear to be Conan 1 specific

    PRINT_RUN_COMMANDS is always on
    (see https://github.com/conan-io/conan/issues/6752#issuecomment-1570619957)

    REVISIONS are always on
    """

    PRINT_RUN_COMMANDS = "log.print_run_commands"
    REVISIONS = "general.revisions_enabled"
