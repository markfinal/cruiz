#!/usr/bin/env python3

"""
Stream data via a multiprocessing queue
"""

from __future__ import annotations

import multiprocessing
import six
import typing

from .colorarma_conversion import convert_from_colorama_to_html

from cruiz.workers.utils.message import Message


if False:
    import io

    # Conan 1.30.0+ changed the assumptions on the base-class of streams used in their
    # runner output to be based from six, so this Python 3 implementation is no longer
    # valid it may come back in future Conan versions that are Python 3 only
    class QueuedStreamPy3(io.RawIOBase):
        """
        A stream class that uses multiprocessing.Queue to send messages
        """

        def __init__(self, queue: multiprocessing.Queue[Message], message_type):
            super().__init__()
            self._queue = queue
            self._message_type = message_type

        # configure the IOBase
        def seekable(self):
            """
            Stream is not seekable
            """
            return False

        def writeable(self):
            """
            Stream is writeable
            """
            # pylint: disable=no-self-use
            return True

        def readable(self):
            """
            Stream is not readable
            """
            return False

        def isatty(self):
            """
            Stream is not interactive
            """
            # TODO: could this be True, which asks the queue for info?
            return False

        # implement functions of interest
        def write(self, message):
            """
            Write a message.
            """
            lines = message.split("\n")
            for line in lines:
                if not line:
                    continue
                self._queue.put(self._message_type(convert_from_colorama_to_html(line)))

        def flush(self):
            """
            Flush the stream.
            """


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
