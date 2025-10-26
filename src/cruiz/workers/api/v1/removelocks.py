#!/usr/bin/env python3

"""Child process commands."""

from __future__ import annotations

import typing

from cruizlib.interop.message import Message, Success

from . import worker

if typing.TYPE_CHECKING:
    import multiprocessing

    from cruizlib.interop.commandparameters import CommandParameters


def invoke(queue: multiprocessing.Queue[Message], params: CommandParameters) -> None:
    """Run 'conan remove --locks'."""
    with worker.ConanWorker(queue, params) as api:
        result = api.remove_locks()

        queue.put(Success(result))
