"""Test the Conan command functionality, using multiple processes, for failure."""

from __future__ import annotations

import logging
import threading
import typing

import cruizlib.workers.api as workers_api
from cruizlib.interop.message import Success

# pylint: disable=wrong-import-order
import pytest

# pylint: disable=import-error
import testexceptions

if typing.TYPE_CHECKING:
    from cruizlib.interop.message import Message
    from cruizlib.multiprocessingmessagequeuetype import (
        MultiProcessingMessageQueueType,
    )


def test_end_watcher_thread(
    multiprocess_reply_queue_fixture: typing.Tuple[
        MultiProcessingMessageQueueType,
        typing.List[Message],
        threading.Thread,
        typing.Any,
    ],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """
    Test: Explicitly end the watcher thread.

    Does not need a local cache as it does not use a Worker.
    """
    caplog.set_level(logging.INFO)

    worker = workers_api.endmessagethread.invoke
    reply_queue, replies, watcher_thread, context = multiprocess_reply_queue_fixture

    process = context.Process(target=worker, args=(reply_queue,))
    process.start()
    process.join()
    watcher_thread.join(timeout=5.0)
    if watcher_thread.is_alive():
        raise testexceptions.WatcherThreadTimeoutError()

    assert "EndOfLine" in caplog.text
    assert replies
    assert isinstance(replies[0], Success)
    assert replies[0].payload is None
