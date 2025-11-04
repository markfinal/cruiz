"""
Test the Conan command functionality, in a single process, for failure.

Note that this is not how cruiz tends to work, and should be using multiple processes
to isolate the Conan commands, but this test shows it still works without that
added complexity.
"""

from __future__ import annotations

import logging
import queue
import threading
import typing

import cruizlib.workers.api as workers_api
from cruizlib.interop.commandparameters import CommandParameters

# pylint: disable=wrong-import-order
import pytest

# pylint: disable=import-error
import testexceptions

if typing.TYPE_CHECKING:
    from cruizlib.interop.message import Message


LOGGER = logging.getLogger(__name__)


def test_expected_failure(
    reply_queue_fixture: typing.Tuple[
        queue.Queue[Message], typing.List[Message], threading.Thread
    ],
    conan_local_cache: typing.Dict[str, str],
) -> None:
    """Test: running conan install incorrect setup, so has an expected failure."""
    worker = workers_api.install.invoke
    params = CommandParameters("install", worker)
    params.added_environment = conan_local_cache
    reply_queue, _, watcher_thread = reply_queue_fixture
    # abusing the type system, as the API used for queue.Queue is the same
    # as for multiprocessing.Queue
    worker(reply_queue, params)  # type: ignore[arg-type]
    with pytest.raises(testexceptions.FailedMessageTestError):
        watcher_thread.join(timeout=5.0)
        if watcher_thread.is_alive():
            raise testexceptions.WatcherThreadTimeoutError()
