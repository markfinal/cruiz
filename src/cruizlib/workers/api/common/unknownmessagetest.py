#!/usr/bin/env python3

"""Test an unknown reply."""

from __future__ import annotations

import contextlib
import typing

from cruizlib.interop.message import End

if typing.TYPE_CHECKING:
    from cruizlib.multiprocessingmessagequeuetype import MultiProcessingMessageQueueType


def invoke(queue: MultiProcessingMessageQueueType) -> None:
    """Return an unknown message type."""
    queue.put(42)  # type: ignore[arg-type]
    queue.put(End())
    with contextlib.suppress(AttributeError):
        # may throw exception if used with a queue.queue rather than multiprocessing
        queue.close()
        queue.join_thread()
