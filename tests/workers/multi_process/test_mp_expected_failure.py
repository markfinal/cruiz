"""Test the Conan command functionality, using multiple processes, for failure."""

from __future__ import annotations

import threading
import typing

import cruizlib.workers.api as workers_api
from cruizlib.interop.commandparameters import CommandParameters

# pylint: disable=wrong-import-order
import pytest

import testexceptions

if typing.TYPE_CHECKING:
    from cruizlib.interop.message import Message
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
    conan_local_cache: typing.Dict[str, str],
) -> None:
    """Test: running conan install incorrect setup, so has an expected failure."""
    worker = workers_api.install.invoke
    params = CommandParameters("install", worker)
    params.added_environment = conan_local_cache
    reply_queue, _, watcher_thread, context = multiprocess_reply_queue_fixture

    process = context.Process(target=worker, args=(reply_queue, params))
    process.start()
    process.join()
    with pytest.raises(testexceptions.FailedMessageTestError):
        watcher_thread.join(timeout=5.0)
        if watcher_thread.is_alive():
            raise testexceptions.WatcherThreadTimeoutError()
