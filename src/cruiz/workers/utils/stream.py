#!/usr/bin/env python3

"""
Stream data via a multiprocessing queue
"""

from __future__ import annotations

import multiprocessing
import six
import typing

from .colorarma_conversion import convert_from_colorama_to_html

from cruiz.interop.message import Message


class QueuedStreamSix(six.StringIO):
    """
    A stream class that uses multiprocessing.Queue to send messages.
    Complete messages may be passed piecemeal, so that coloured output is generated.
    This buffers up a message, so that it is passed across the process divide as a
    single HTML paragraph.
    """

    def __init__(
        self, queue: multiprocessing.Queue[Message], message_type: typing.Any
    ) -> None:
        super().__init__()
        self._queue = queue
        self._message_type = message_type
        self._block = six.StringIO()

    def write(self, message: str) -> int:
        """
        Write a message.
        """
        result = self._block.write(convert_from_colorama_to_html(message))
        if message.endswith("\n"):
            self._queue.put(self._message_type(self._block.getvalue()))
            self._block = six.StringIO()
        return result
