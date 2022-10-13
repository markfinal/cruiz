#!/usr/bin/env python3

"""
Conan config entries of interest
"""

from enum import Enum


class ConanConfigBoolean(Enum):
    """
    Enumeration for Conan configuration items that are Boolean values
    """

    PRINT_RUN_COMMANDS = "log.print_run_commands"
    REVISIONS = "general.revisions_enabled"
