#!/usr/bin/env python3

"""
Run an arbtitrary Conan command.

It must match one of the Conan verbs though.
"""

from __future__ import annotations

import multiprocessing
import typing

from cruiz.interop.message import Failure, Message, Success

from . import worker

if typing.TYPE_CHECKING:
    from cruiz.interop.commandparameters import CommandParameters


def invoke(queue: multiprocessing.Queue[Message], params: CommandParameters) -> None:
    """Run an arbitrary command."""
    with worker.ConanWorker(queue, params):
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
                if exc.code:
                    raise RuntimeError(temp_err.getvalue())
                queue.put(Success(temp_out.getvalue()))
            except RuntimeError as exc_inner:
                queue.put(Failure(exc_inner))
        finally:
            sys.stderr = sys.__stderr__
            sys.stdout = sys.__stdout__
            sys.argv = saved_args
