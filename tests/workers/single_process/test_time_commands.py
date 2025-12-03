"""
Test the timing of the duration of a conan command, in a single process.

Note that this is not how cruiz tends to work, and should be using multiple processes
to isolate the Conan commands, but this test shows it still works without that
added complexity.
"""

import logging
import queue
import threading
import typing

import cruizlib.workers.api as workers_api
from cruizlib.interop.commandparameters import CommandParameters
from cruizlib.interop.message import (
    Message,
    Success,
)

# pylint: disable=wrong-import-order
import pytest

import texceptions


LOGGER = logging.getLogger(__name__)


def test_conan_time_command_duration(
    reply_queue_fixture: typing.Callable[
        [], typing.Tuple[queue.Queue[Message], typing.List[Message], threading.Thread]
    ],
    conan_local_cache: typing.Dict[str, str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test: enabling time_commands in params to enable wall clock timing."""
    caplog.set_level(logging.INFO)
    worker = workers_api.removeallpackages.invoke
    params = CommandParameters("removeallpackages", worker)
    params.added_environment = conan_local_cache
    params.time_commands = True
    reply_queue, replies, watcher_thread = reply_queue_fixture()
    # abusing the type system, as the API used for queue.Queue is the same
    # as for multiprocessing.Queue
    worker(reply_queue, params)  # type: ignore[arg-type]
    watcher_thread.join(timeout=5.0)
    if watcher_thread.is_alive():
        raise texceptions.WatcherThreadTimeoutError()

    assert replies
    assert isinstance(replies[0], Success)
    assert isinstance(replies[0].payload, bool)
    assert replies[0].payload

    assert "ran in" in caplog.text
