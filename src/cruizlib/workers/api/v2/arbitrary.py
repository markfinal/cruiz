#!/usr/bin/env python3

"""
Run an arbtitrary Conan command.

It must match one of the Conan verbs though.
"""

from __future__ import annotations

import typing

from cruizlib.interop.message import Failure, Success

from . import worker

if typing.TYPE_CHECKING:
    from cruizlib.interop.commandparameters import CommandParameters
    from cruizlib.multiprocessingmessagequeuetype import MultiProcessingMessageQueueType


def invoke(queue: MultiProcessingMessageQueueType, params: CommandParameters) -> None:
    """Run an arbitrary command."""
    with worker.ConanWorker(queue, params):
        # pylint: disable=import-outside-toplevel
        from conans.conan import run
        from io import StringIO
        import sys

        saved_args = sys.argv
        temp_out = StringIO()
        temp_err = StringIO()
        sys.stdout = temp_out
        sys.stderr = temp_err
        try:
            sys.argv = ["conan", params.verb] + params.arguments
            run()
        except SystemExit as exc:
            try:
                # pylint: disable=using-constant-test
                if exc.code:
                    raise RuntimeError(temp_err.getvalue()) from exc
                queue.put(Success(temp_out.getvalue()))
            except RuntimeError as exc_inner:
                queue.put(Failure(exc_inner))
        finally:
            sys.stderr = sys.__stderr__
            sys.stdout = sys.__stdout__
            sys.argv = saved_args
