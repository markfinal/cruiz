"""Test the Conan command functionality, using multiple processes, for failure."""

from __future__ import annotations

import typing

import cruizlib.workers.api as workers_api
from cruizlib.interop.commandparameters import CommandParameters

# pylint: disable=wrong-import-order
import pytest

import texceptions

if typing.TYPE_CHECKING:
    from ttypes import MultiprocessReplyQueueFixture


def test_expected_failure(
    multiprocess_reply_queue_fixture: MultiprocessReplyQueueFixture,
    conan_local_cache: typing.Dict[str, str],
) -> None:
    """Test: running conan install incorrect setup, so has an expected failure."""
    worker = workers_api.install.invoke
    params = CommandParameters("install", worker)
    params.added_environment = conan_local_cache
    reply_queue, _, watcher_thread, context = multiprocess_reply_queue_fixture()

    process = context.Process(target=worker, args=(reply_queue, params))
    process.start()
    process.join()
    with pytest.raises(texceptions.FailedMessageTestError):
        watcher_thread.join(timeout=5.0)
        if watcher_thread.is_alive():
            raise texceptions.WatcherThreadTimeoutError()
