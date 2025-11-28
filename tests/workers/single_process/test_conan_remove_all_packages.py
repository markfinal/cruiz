"""
Test the conan remove (all packages) functionality, in a single process.

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
import testexceptions


LOGGER = logging.getLogger(__name__)


def test_conan_remove_all_packages(
    reply_queue_fixture: typing.Callable[
        [], typing.Tuple[queue.Queue[Message], typing.List[Message], threading.Thread]
    ],
    conan_local_cache: typing.Dict[str, str],
) -> None:
    """Test: running conan remove (for all packages)."""
    worker = workers_api.removeallpackages.invoke
    params = CommandParameters("package", worker)
    params.added_environment = conan_local_cache
    reply_queue, replies, watcher_thread = reply_queue_fixture()
    # abusing the type system, as the API used for queue.Queue is the same
    # as for multiprocessing.Queue
    worker(reply_queue, params)  # type: ignore[arg-type]
    watcher_thread.join(timeout=5.0)
    if watcher_thread.is_alive():
        raise testexceptions.WatcherThreadTimeoutError()

    assert replies
    assert isinstance(replies[0], Success)
    assert isinstance(replies[0].payload, bool)
    assert replies[0].payload
