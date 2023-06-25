#!/usr/bin/env python3

"""
Utils for worker context managers for Conan v2
"""

from __future__ import annotations

import multiprocessing
import typing

from cruiz.workers.utils.worker import Worker
from cruiz.workers.utils.stream import QueuedStreamSix

from cruiz.interop.message import Message, Stdout, Stderr


def _patch_conan_output_initialiser(queue: multiprocessing.Queue[Message]) -> None:
    # this has to be the first import of ConanOutput
    from conan.api.output import ConanOutput

    conanoutput_old_init = ConanOutput.__init__

    def new_init(self: ConanOutput, scope: str = "") -> None:
        conanoutput_old_init(self, scope)
        self.stream = QueuedStreamSix(queue, Stdout)

    ConanOutput.__init__ = new_init


def _patch_conan_run(queue: multiprocessing.Queue[Message]) -> None:
    # this has to be the first import of conan_run
    import conans

    conanrun_old = conans.util.runners.conan_run

    def new_conan_run(  # type: ignore[no-untyped-def]
        command, stdout=None, stderr=None, cwd=None, shell=True
    ):
        stdout_stream = QueuedStreamSix(queue, Stdout)
        stderr_stream = QueuedStreamSix(queue, Stderr)
        return conanrun_old(command, stdout_stream, stderr_stream, cwd, shell)

    conans.util.runners.conan_run = new_conan_run


def _do_patching(queue: multiprocessing.Queue[Message]) -> None:
    _patch_conan_output_initialiser(queue)
    _patch_conan_run(queue)


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
        from conan.api.conan_api import ConanAPI

        _do_patching(self._queue)

        return ConanAPI()
