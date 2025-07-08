#!/usr/bin/env python3

"""
Send a message to indicate it's the end of data.

Thenclose down this side of the message queue.
"""

from __future__ import annotations

import typing

from cruizlib.interop.message import End, Message

if typing.TYPE_CHECKING:
    import multiprocessing


def invoke(queue: multiprocessing.Queue[Message]) -> None:
    """Run an arbitrary command."""
    queue.put(End())
    queue.close()
    queue.join_thread()
