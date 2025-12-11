#!/usr/bin/env python3

"""Test a Failure reply."""

from __future__ import annotations

import contextlib
import traceback
import typing

from cruizlib.interop.message import End, Failure

if typing.TYPE_CHECKING:
    from cruizlib.multiprocessingmessagequeuetype import MultiProcessingMessageQueueType


def invoke(queue: MultiProcessingMessageQueueType, html: typing.Optional[str]) -> None:
    """Return a failed message."""
    try:
        raise ValueError("Failed Test!")
    except ValueError as exc:
        failure = Failure(
            str(exc), type(exc).__name__, traceback.format_tb(exc.__traceback__)
        )
        if html is not None:
            failure.html = html
        queue.put(failure)
    queue.put(End())
    with contextlib.suppress(AttributeError):
        # may throw exception if used with a queue.queue rather than multiprocessing
        queue.close()
        queue.join_thread()
