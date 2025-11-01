"""Test the Conan command functionality, using multiple processes."""

from __future__ import annotations

import threading
import typing

import cruizlib.workers.api as workers_api
from cruizlib.interop.commandparameters import CommandParameters
from cruizlib.interop.message import Failure, Message

if typing.TYPE_CHECKING:
    from cruizlib.multiprocessingmessagequeuetype import (
        MultiProcessingMessageQueueType,
    )


def test_expected_failure(
    multiprocess_reply_queue_fixture: typing.Tuple[
        MultiProcessingMessageQueueType,
        typing.List[Message],
        threading.Thread,
        typing.Any,
    ],
) -> None:
    """Test: running conan install incorrect setup, so has an expected failure."""
    worker = workers_api.install.invoke
    params = CommandParameters("install", worker)
    reply_queue, replies, watcher_thread, context = multiprocess_reply_queue_fixture

    process = context.Process(target=worker, args=(reply_queue, params))
    process.start()
    process.join()
    watcher_thread.join()

    assert replies
    assert isinstance(replies[0], Failure)
