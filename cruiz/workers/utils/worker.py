#!/usr/bin/env python3

"""
Utils for worker context managers
"""

from __future__ import annotations

import datetime
import multiprocessing
import os
import traceback
import typing

from qtpy import QtCore

from cruiz.interop.commandparameters import CommandParameters
from cruiz.interop.commonparameters import CommonParameters
from cruiz.interop.searchrecipesparameters import SearchRecipesParameters
from cruiz.interop.reciperevisionsparameters import RecipeRevisionsParameters
from cruiz.interop.packagerevisionsparameters import PackageRevisionsParameters
from cruiz.interop.packageidparameters import PackageIdParameters
from cruiz.interop.packagebinaryparameters import PackageBinaryParameters

from .env import set_env, clear_conan_env
from .message import Message, Failure, Stdout
from .text2html import text_to_html


class Worker:
    """
    Non-Conan specific worker context manager
    """

    # TODO: tried to use typing.Type[CommonParameters] here but mypy didn't like it
    def __init__(
        self,
        queue: multiprocessing.Queue[Message],
        params: typing.Union[
            CommandParameters,
            SearchRecipesParameters,
            RecipeRevisionsParameters,
            PackageRevisionsParameters,
            PackageIdParameters,
            PackageBinaryParameters,
        ],
    ):
        self._queue = queue
        self._params = params
        if isinstance(params, CommandParameters):
            self._wall_clock = QtCore.QElapsedTimer() if params.time_commands else None
        else:
            # can occur for other types of *Parameters classes
            self._wall_clock = None

    def __enter__(self) -> None:
        multiprocessing.get_logger().debug("%i (child): %s", os.getpid(), self._params)
        clear_conan_env()
        if isinstance(self._params, CommandParameters):
            set_env(self._params.added_environment, self._params.removed_environment)
        elif isinstance(self._params, CommonParameters):
            set_env(self._params.added_environment, self._params.removed_environment)
        else:
            try:
                if "env" in self._params:
                    set_env(self._params["env"], [])
            except TypeError:
                # can happen for other types of *Parameters classes
                pass

        if self._wall_clock is not None:
            self._wall_clock.start()

    def _exception_to_html(
        self, exc_type: typing.Any, value: typing.Any, exc_tb: typing.Any
    ) -> None:
        # pylint: disable=unused-argument

        # since tracebacks objects can't be passed over the multiprocessing queue,
        # encode it into the string of a new Exception object
        # (also removes the issue of Conan exception types passing the divide)
        exc_text = traceback.format_exception(exc_type, value, exc_tb)
        html = "<font color='red'>"
        html += text_to_html("".join(exc_text))
        html += "</font>"

        self._queue.put(Failure(Exception(html)))

        multiprocessing.get_logger().debug(
            "%i (child): Exception detected: %s",
            os.getpid(),
            exc_text,
        )

    def __exit__(
        self, exc_type: typing.Any, exc_value: typing.Any, exc_traceback: typing.Any
    ) -> typing.Any:
        if exc_value:
            self._exception_to_html(exc_type, exc_value, exc_traceback)
        if self._wall_clock is not None:
            elapsed_time = self._wall_clock.elapsed()
            self._queue.put(Stdout("-" * 64))
            if isinstance(self._params, CommandParameters):
                worker = self._params.worker
            else:
                # TODO: does this get used any more?
                worker = self._params["worker"]  # type: ignore
            self._queue.put(
                Stdout(
                    f"Command {worker} ran in "
                    f"{datetime.timedelta(seconds=elapsed_time / 1000)}"
                )
            )
            self._queue.put(Stdout("-" * 64))
        self._queue.close()
        self._queue.join_thread()
        return True  # suppress further exception propogation


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
            try:
                for component_key in cpp_info["components"]:
                    component = cpp_info["components"][component_key]
                    component["version"] = str(component["version"])
            except KeyError:
                # ignore 'components' not being in cpp_info
                pass
            try:
                build_modules: typing.Dict[str, str] = {}
                for key, value in cpp_info["build_modules"].items():
                    build_modules[key] = value
                cpp_info["build_modules"] = build_modules
            except KeyError:
                # ignore 'build_modules' not being in cpp_info
                pass
