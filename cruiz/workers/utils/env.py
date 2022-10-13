#!/usr/bin/env python3

"""
Util to set the process' environment
"""

import multiprocessing
import os
import typing


def clear_conan_env() -> None:
    """
    cruiz needs to control all Conan environments, so ignore everything from
    the calling environment
    """
    external_conan_envvar_names = [
        key for key, _ in os.environ.items() if key.startswith("CONAN_")
    ]
    if external_conan_envvar_names:
        multiprocessing.get_logger().debug(
            "Removing the following environment variables from cruiz's process:"
        )
        for key in external_conan_envvar_names:
            multiprocessing.get_logger().debug("\t%s", key)
            os.environ.pop(key)


def set_env(
    additions: typing.Dict[str, typing.Any], removals: typing.List[str]
) -> None:
    """
    Set the environment given key-value pairs to add, and keys to remove.
    If a key is added, and already exists in the public environment map,
    then it is prepended with a path separator.
    """
    for key, value in additions.items():
        if value is None:
            continue
        if not isinstance(value, str):
            value = str(value)
        if key in os.environ:
            if value not in os.environ[key]:
                os.environ[key] = value + os.pathsep + os.environ[key]
        else:
            os.environ[key] = value
    for key in removals:
        if key in os.environ:
            os.environ.pop(key)
