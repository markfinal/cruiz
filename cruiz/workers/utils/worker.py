#!/usr/bin/env python3

"""
Utils for worker context managers
"""

from __future__ import annotations

import contextlib
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
from cruiz.interop.message import Message, Failure, Stdout

from cruiz.workers.utils.env import set_env, clear_conan_env
from cruiz.workers.utils.text2html import text_to_html


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
        if isinstance(self._params, (CommandParameters, CommonParameters)):
            set_env(self._params.added_environment, self._params.removed_environment)
        else:
            with contextlib.suppress(TypeError):  # type: ignore[unreachable]
                # can happen for other types of *Parameters classes
                if "env" in self._params:
                    set_env(self._params["env"], [])

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
