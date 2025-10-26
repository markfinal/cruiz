#!/usr/bin/env python3

"""Child process commands."""

from __future__ import annotations

import typing

from cruizlib.interop.message import Message, Stdout, Success

from . import worker

if typing.TYPE_CHECKING:
    import multiprocessing

    from cruizlib.interop.commandparameters import CommandParameters


def invoke(queue: multiprocessing.Queue[Message], params: CommandParameters) -> None:
    """Run 'conan remove [-f] *'."""
    with worker.ConanWorker(queue, params) as api:
        force = True
        result = api.remove("*", force=force)
        queue.put(
            Stdout(
                "Removed all packages from the local cache" " (forced)" if force else ""
            )
        )

        queue.put(Success(result))
