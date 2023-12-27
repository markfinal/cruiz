#!/usr/bin/env python3

"""
Utils for worker context managers for Conan v1
"""

import contextlib
import typing

from cruiz.workers.utils.worker import Worker


# pylint: disable=too-few-public-methods
class ConanWorker(Worker):
    """
    Conan specific context manager
    """

    def __enter__(self) -> typing.Any:
        super().__enter__()
        # import here because it can use the environment variables set in the
        # super class
        # pylint: disable=import-outside-toplevel
        from .conanapi import instance

        api = instance(self._queue, self._params)
        return api


def replace_conan_version_struct_with_string(
    result: typing.Dict[typing.Any, typing.Any]
) -> None:
    """
    Results have ConanVersion structs, but these cannot be passed over the
    process divide so just convert them to strings
    """
    if "installed" not in result:
        return
    for installed in result["installed"]:
        recipe = installed["recipe"]
        recipe["version"] = str(recipe["version"])
        for package in installed["packages"]:
            try:
                cpp_info = package["cpp_info"]
            except KeyError:
                # no cpp_info, so abort further processing
                continue
            cpp_info["version"] = str(cpp_info["version"])
            with contextlib.suppress(KeyError):
                # ignore 'components' not being in cpp_info
                for component_key in cpp_info["components"]:
                    component = cpp_info["components"][component_key]
                    component["version"] = str(component["version"])
            with contextlib.suppress(KeyError):
                # ignore 'build_modules' not being in cpp_info
                build_modules: typing.Dict[str, str] = {}
                for key, value in cpp_info["build_modules"].items():
                    build_modules[key] = value
                cpp_info["build_modules"] = build_modules
