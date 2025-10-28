#!/usr/bin/env python3

"""Child process commands."""

from __future__ import annotations

import typing

from cruizlib.interop.message import Stdout, Success

from . import worker

if typing.TYPE_CHECKING:
    from cruizlib.interop.commandparameters import CommandParameters
    from cruizlib.multiprocessingmessagequeuetype import MultiProcessingMessageQueueType


def invoke(queue: MultiProcessingMessageQueueType, params: CommandParameters) -> None:
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
