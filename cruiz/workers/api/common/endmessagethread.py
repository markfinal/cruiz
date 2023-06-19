#!/usr/bin/env python3

"""
Send a message to indicate it's the end of data, and close down
this side of the message queue.
"""

from __future__ import annotations

import multiprocessing

from cruiz.interop.message import Message, End


def invoke(queue: multiprocessing.Queue[Message]) -> None:
    """
    Run an arbitrary command
    """
    queue.put(End())
    queue.close()
    queue.join_thread()
