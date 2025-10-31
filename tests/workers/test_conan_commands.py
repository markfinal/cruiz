"""Test the Conan command functionality, using multiple processes."""

from __future__ import annotations

import contextlib
import logging
import multiprocessing
import threading
import typing

import cruizlib.workers.api as workers_api
from cruizlib.interop.commandparameters import CommandParameters
from cruizlib.interop.message import (
    ConanLogMessage,
    Failure,
    Message,
    Stderr,
    Stdout,
    Success,
)

if typing.TYPE_CHECKING:
    from cruizlib.multiprocessingmessagequeuetype import (
        MultiProcessingMessageQueueType,
    )


LOGGER = logging.getLogger(__name__)


def _queue_watcher(
    reply_queue: MultiProcessingMessageQueueType, replies: typing.List[Message]
) -> None:
    try:
        while True:
            reply = reply_queue.get()
            if isinstance(reply, (Success, Failure)):
                replies.append(reply)
                break
            if isinstance(reply, (ConanLogMessage, Stdout, Stderr)):
                LOGGER.info("Message: '%s'", reply.message)
                continue
            raise ValueError(f"Unknown reply of type '{type(reply)}'")
    finally:
        reply_queue.close()
        reply_queue.join_thread()


@contextlib.contextmanager
def _watcher(
    reply_queue: MultiProcessingMessageQueueType,
) -> typing.Generator[typing.List[Message], None, None]:
    replies: typing.List[Message] = []
    watcher_thread = threading.Thread(
        target=_queue_watcher, args=(reply_queue, replies)
    )
    watcher_thread.start()
    yield replies
    watcher_thread.join()


def test_expected_failure() -> None:
    """Test: running conan install incorrect setup, so has an expected failure."""
    worker = workers_api.install.invoke
    params = CommandParameters("install", worker)

    context = multiprocessing.get_context("spawn")
    reply_queue = context.Queue()
    with _watcher(reply_queue) as replies:
        process = context.Process(target=worker, args=(reply_queue, params))
        process.start()
        process.join()
    assert replies
    assert isinstance(replies[0], Failure)
