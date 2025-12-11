#!/usr/bin/env python3

"""Test the messaging system."""

from __future__ import annotations

import contextlib
import typing

from cruizlib.interop.message import ConanLogMessage, End, Stderr, Stdout

if typing.TYPE_CHECKING:
    from cruizlib.multiprocessingmessagequeuetype import MultiProcessingMessageQueueType


def invoke(queue: MultiProcessingMessageQueueType) -> None:
    """Run messaging commands."""
    queue.put(Stdout("Stdout Test"))
    queue.put(Stderr("Stderr Test"))
    queue.put(ConanLogMessage("ConanLogMessage Test"))
    queue.put(End())
    with contextlib.suppress(AttributeError):
        # may throw exception if used with a queue.queue rather than multiprocessing
        queue.close()
        queue.join_thread()
