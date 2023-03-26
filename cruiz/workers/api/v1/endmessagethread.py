#!/usr/bin/env python3

"""
Child process commands
"""

from __future__ import annotations

import multiprocessing

from .utils.message import Message, End


def invoke(queue: multiprocessing.Queue[Message]) -> None:
    """
    Run an arbitrary command
    """
    queue.put(End())
    queue.close()
    queue.join_thread()
