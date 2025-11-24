#!/usr/bin/env python3

"""Utils for worker context managers."""

from __future__ import annotations

import contextlib
import datetime
import multiprocessing
import os
import traceback
import types
import typing

from PySide6 import QtCore

from cruizlib.interop.commandparameters import CommandParameters
from cruizlib.interop.commonparameters import CommonParameters
from cruizlib.interop.message import Failure, Stdout
from cruizlib.workers.utils.env import clear_conan_env, set_env
from cruizlib.workers.utils.text2html import text_to_html

if typing.TYPE_CHECKING:
    from cruiz.interop.packagebinaryparameters import PackageBinaryParameters
    from cruiz.interop.packageidparameters import PackageIdParameters
    from cruiz.interop.packagerevisionsparameters import PackageRevisionsParameters
    from cruiz.interop.reciperevisionsparameters import RecipeRevisionsParameters

    from cruizlib.interop.searchrecipesparameters import SearchRecipesParameters
    from cruizlib.multiprocessingmessagequeuetype import MultiProcessingMessageQueueType


class Worker:
    """Non-Conan specific worker context manager."""

    # TODO: tried to use typing.Type[CommonParameters] here but mypy didn't like it
    def __init__(
        self,
        reply_queue: MultiProcessingMessageQueueType,
        params: typing.Union[
            CommandParameters,
            SearchRecipesParameters,
            RecipeRevisionsParameters,
            PackageRevisionsParameters,
            PackageIdParameters,
            PackageBinaryParameters,
        ],
    ):
        """Initialise a Worker."""
        self._queue = reply_queue
        self._params = params
        if isinstance(params, CommandParameters):
            self._wall_clock = QtCore.QElapsedTimer() if params.time_commands else None
        else:
            # can occur for other types of *Parameters classes
            self._wall_clock = None

    def __enter__(self) -> None:
        """Enter a context manager with a Worker."""
        multiprocessing.get_logger().debug("%i (child): %s", os.getpid(), self._params)
        clear_conan_env()
        if isinstance(self._params, (CommandParameters, CommonParameters)):
            set_env(self._params.added_environment, self._params.removed_environment)
        else:
            with contextlib.suppress(TypeError):
                # can happen for other types of *Parameters classes
                if "env" in self._params:
                    set_env(self._params["env"], [])

        if self._wall_clock is not None:
            self._wall_clock.start()

    def _raise_failure_to_caller(
        self,
        exc_type: typing.Optional[type[BaseException]],
        exc_value: typing.Optional[BaseException],
        exc_traceback: types.TracebackType,
    ) -> None:
        exception_message = str(exc_value)
        failure = Failure(
            exception_message,
            exc_type.__name__ if exc_type else "",
            traceback.format_tb(exc_traceback),
        )

        exc_text = traceback.format_exception(exc_type, exc_value, exc_traceback)
        # since tracebacks objects can't be passed over the multiprocessing queue,
        # encode it into the string of a new Exception object
        # (also removes the issue of Conan exception types passing the divide)
        html = "<font color='red'>"
        html += text_to_html("".join(exc_text))
        html += "</font>"

        failure.html = html

        self._queue.put(failure)

        multiprocessing.get_logger().debug(
            "%i (child): Exception detected: %s",
            os.getpid(),
            exc_text,
        )

    def __exit__(
        self,
        exc_type: typing.Optional[type[BaseException]],
        exc_value: typing.Optional[BaseException],
        exc_traceback: types.TracebackType,
    ) -> typing.Any:
        """Exit a context manager with a Worker."""
        if exc_value:
            self._raise_failure_to_caller(exc_type, exc_value, exc_traceback)
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
        with contextlib.suppress(AttributeError):
            # in single process tests, self._queue is not a multiprocessing.Queue
            # and does not have these methods
            self._queue.close()
            self._queue.join_thread()
        return True  # suppress further exception propogation
