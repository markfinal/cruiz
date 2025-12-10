#!/usr/bin/env python3

"""
Send a message to indicate it's the end of data.

Thenclose down this side of the message queue.
"""

from __future__ import annotations

import contextlib
import typing

from cruizlib.interop.message import End

if typing.TYPE_CHECKING:
    from cruizlib.multiprocessingmessagequeuetype import MultiProcessingMessageQueueType


def invoke(queue: MultiProcessingMessageQueueType) -> None:
    """Run an arbitrary command."""
    queue.put(End())
    with contextlib.suppress(AttributeError):
        # may throw exception if used with a queue.queue rather than multiprocessing
        queue.close()
        queue.join_thread()
