"""
Test the Conan command functionality, in a single process.

Note that this is not how cruiz tends to work, and should be using multiple processes
to isolate the Conan commands, but this test shows it still works without that
added complexity.
"""

from __future__ import annotations

import contextlib
import logging
import queue
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


LOGGER = logging.getLogger(__name__)


def _queue_watcher_local(
    reply_queue: queue.Queue[Message], replies: typing.List[Message]
) -> None:
    while True:
        reply = reply_queue.get()
        if isinstance(reply, (Success, Failure)):
            replies.append(reply)
            break
        if isinstance(reply, (ConanLogMessage, Stdout, Stderr)):
            LOGGER.info("Message: '%s'", reply.message)
            continue
        raise ValueError(f"Unknown reply of type '{type(reply)}'")


@contextlib.contextmanager
def _watcher_local(
    reply_queue: queue.Queue[Message],
) -> typing.Generator[typing.List[Message], None, None]:
    replies: typing.List[Message] = []
    watcher_thread = threading.Thread(
        target=_queue_watcher_local, args=(reply_queue, replies)
    )
    watcher_thread.start()
    yield replies
    watcher_thread.join()


def test_expected_failure_single_process() -> None:
    """Test: running conan install incorrect setup, so has an expected failure."""
    worker = workers_api.install.invoke
    params = CommandParameters("install", worker)

    reply_queue = queue.Queue[Message]()
    with _watcher_local(reply_queue) as replies:
        # abusing the type system, as the API used for queue.Queue is the same
        # as for multiprocessing.Queue
        worker(reply_queue, params)  # type: ignore[arg-type]
    assert replies
    assert isinstance(replies[0], Failure)
