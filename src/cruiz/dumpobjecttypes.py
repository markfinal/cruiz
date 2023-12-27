#!/usr/bin/env python3

"""
Debug utility to recursively identify all the types of all attributes in an object.
Useful to figure out if Conan types made it across the process divide.

Define CRUIZ_DUMP_OBJECT_TYPES_DETAIL in the environment to show more detailed object
information (which is much harder to read).
"""

import logging
import os
import typing

logger = logging.getLogger(__name__)

__VISITED: typing.List[typing.Any] = []


def __examine(obj: typing.Any, loglevel: int, depth: int, prefix: str = "") -> None:
    if id(obj) in __VISITED:
        return
    __VISITED.append(id(obj))
    indent = depth * " "
    if "CRUIZ_DUMP_OBJECT_TYPES_DETAIL" in os.environ:
        logger.log(loglevel, "%s%s%s (%s)", indent, prefix, type(obj), obj.__repr__)
    else:
        logger.log(loglevel, "%s%s%s", indent, prefix, type(obj))
    if isinstance(obj, (list, tuple)):
        for i, item in enumerate(obj):
            __examine(item, loglevel, depth + 1, f"{i}: ")
    elif isinstance(obj, (str, bool)):
        pass
    elif isinstance(obj, dict):
        for key, value in obj.items():
            __examine(value, loglevel, depth + 1, f"{key}: ")
    elif obj is not None:
        try:
            dict_of_attribs = obj.__dict__
            for key, value in dict_of_attribs.items():
                __examine(value, loglevel, depth + 1, f"{key}: ")
        except AttributeError:
            logger.log(
                loglevel,
                "%s\tWARNING: Type is opaque - no attribute information",
                indent,
            )


def dump_object_types(obj: typing.Any, loglevel: str = "DEBUG") -> None:
    """
    Recursively dump the types of all attributes of the specified object
    Optional logging level for the output
    """
    __VISITED.clear()
    __examine(obj, int(logging.getLevelName(loglevel)), 0)
