#!/usr/bin/env python3

"""Test a Successful reply."""

from __future__ import annotations

import contextlib
import typing

from cruizlib.interop.message import End, Success

if typing.TYPE_CHECKING:
    from cruizlib.multiprocessingmessagequeuetype import MultiProcessingMessageQueueType


def invoke(queue: MultiProcessingMessageQueueType) -> None:
    """Return a successful message."""
    queue.put(Success("This was a success!"))
    queue.put(End())
    with contextlib.suppress(AttributeError):
        # may throw exception if used with a queue.queue rather than multiprocessing
        queue.close()
        queue.join_thread()
