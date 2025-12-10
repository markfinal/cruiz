"""
Test the deleting the CMake cache functionality, in a single process, for failure.

Note that this is not how cruiz tends to work, and should be using multiple processes
to isolate the Conan commands, but this test shows it still works without that
added complexity.
"""

from __future__ import annotations

import logging
import pathlib
import typing

import cruizlib.workers.api as workers_api
from cruizlib.globals import CONAN_MAJOR_VERSION
from cruizlib.interop.commandparameters import CommandParameters
from cruizlib.interop.message import Success

# pylint: disable=wrong-import-order
import pytest

if typing.TYPE_CHECKING:
    from ttypes import RunWorkerFixture, SingleprocessReplyQueueFixture


LOGGER = logging.getLogger(__name__)


@pytest.mark.parametrize("build_folder", [None, pathlib.PurePath("buildfolder")])
@pytest.mark.xfail(
    CONAN_MAJOR_VERSION == 2,
    reason="CMake cache deletion command does not exist in Conan 2",
    strict=True,
)
def test_cmake_delete_cache(
    reply_queue_fixture: SingleprocessReplyQueueFixture,
    run_worker: RunWorkerFixture,
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
    reply_queue, replies, watcher_thread, context = reply_queue_fixture()
    run_worker(worker, reply_queue, params, watcher_thread, context)

    assert replies
    assert isinstance(replies[0], Success)
    assert replies[0].payload is None
    assert "Deleted CMake cache at" in caplog.text
