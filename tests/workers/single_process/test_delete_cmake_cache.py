"""
Test the deleting the CMake cache functionality, in a single process, for failure.

Note that this is not how cruiz tends to work, and should be using multiple processes
to isolate the Conan commands, but this test shows it still works without that
added complexity.
"""

from __future__ import annotations

import logging
import pathlib
import queue
import threading
import typing

import cruizlib.workers.api as workers_api
from cruizlib.globals import CONAN_MAJOR_VERSION
from cruizlib.interop.commandparameters import CommandParameters
from cruizlib.interop.message import Success

# pylint: disable=wrong-import-order
import pytest

import testexceptions

if typing.TYPE_CHECKING:
    from cruizlib.interop.message import Message


LOGGER = logging.getLogger(__name__)


@pytest.mark.parametrize("build_folder", [None, pathlib.PurePath("buildfolder")])
@pytest.mark.xfail(
    CONAN_MAJOR_VERSION == 2,
    reason="CMake cache deletion command does not exist in Conan 2",
)
def test_cmake_delete_cache(
    reply_queue_fixture: typing.Callable[
        [], typing.Tuple[queue.Queue[Message], typing.List[Message], threading.Thread]
    ],
    tmp_path: pathlib.Path,
    caplog: pytest.LogCaptureFixture,
    build_folder: typing.Optional[pathlib.PurePath],
) -> None:
    """Test: CMake build tool invocation."""
    caplog.set_level(logging.INFO)

    worker = workers_api.deletecmakecache.invoke
    params = CommandParameters("cmakeremovecache", worker)
    params.cwd = tmp_path
    if build_folder:
        params.build_folder = build_folder
    reply_queue, replies, watcher_thread = reply_queue_fixture()
    # abusing the type system, as the API used for queue.Queue is the same
    # as for multiprocessing.Queue
    worker(reply_queue, params)  # type: ignore[arg-type]
    watcher_thread.join(timeout=5.0)
    if watcher_thread.is_alive():
        raise testexceptions.WatcherThreadTimeoutError()

    assert replies
    assert isinstance(replies[0], Success)
    assert replies[0].payload is None
    assert "Deleted CMake cache at" in caplog.text
