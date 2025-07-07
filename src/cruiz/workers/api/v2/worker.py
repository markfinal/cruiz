#!/usr/bin/env python3

"""Utils for worker context managers for Conan v2."""

from __future__ import annotations

import multiprocessing
import typing

import cruiz.runcommands
from cruiz.interop.message import Message, Stderr, Stdout
from cruiz.workers.utils.stream import QueuedStreamSix
from cruiz.workers.utils.worker import Worker


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
    try:
        import conan
    except ImportError:
        # older than Conan 2.17.0
        import conans

    # entirely replacing the vanilla conan_run, because it uses subprocess communicate
    # which does not stream the output, but waits for the end of the process
    def new_conan_run(  # type: ignore[no-untyped-def]
        command, stdout=None, stderr=None, cwd=None, shell=True
    ):
        # pylint: disable=unused-argument
        with conans.util.runners.pyinstaller_bundle_env_cleaned():
            with cruiz.runcommands.get_popen_for_capture(
                command,
                shell=shell,
                cwd=cwd,
            ) as process:
                assert process.stdout
                for line in iter(process.stdout.readline, ""):
                    queue.put(Stdout(line))
                assert process.stderr
                for line in iter(process.stderr.readline, ""):
                    queue.put(Stderr(line))

            return process.returncode

    try:
        conan.internal.util.runners.conan_run = new_conan_run
    except AttributeError:
        conans.util.runners.conan_run = new_conan_run


def _do_patching(queue: multiprocessing.Queue[Message]) -> None:
    _patch_conan_output_initialiser(queue)
    _patch_conan_run(queue)


class ConanWorker(Worker):
    """Conan specific context manager."""

    def __enter__(self) -> typing.Any:
        """Enter a context manager with a Conan Worker."""
        super().__enter__()
        # import here because it can use the environment variables
        # set in the super class
        from conan.api.conan_api import ConanAPI

        _do_patching(self._queue)

        return ConanAPI()
