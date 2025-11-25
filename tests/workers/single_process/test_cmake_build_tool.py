"""
Test the CMake build tool functionality, in a single process, for failure.

Note that this is not how cruiz tends to work, and should be using multiple processes
to isolate the Conan commands, but this test shows it still works without that
added complexity.
"""

from __future__ import annotations

import logging
import os
import pathlib
import queue
import stat
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


@pytest.mark.xfail(
    CONAN_MAJOR_VERSION == 2,
    reason="CMake build tool command does not exist in Conan 2",
)
def test_cmake_no_cache(
    reply_queue_fixture: typing.Callable[
        [], typing.Tuple[queue.Queue[Message], typing.List[Message], threading.Thread]
    ],
    tmp_path: pathlib.Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test: CMake build tool invocation."""
    caplog.set_level(logging.INFO)

    worker = workers_api.cmakebuildtool.invoke
    params = CommandParameters("cmakebuild", worker)
    params.cwd = tmp_path
    # params.added_environment = conan_local_cache
    reply_queue, _, watcher_thread = reply_queue_fixture()
    # abusing the type system, as the API used for queue.Queue is the same
    # as for multiprocessing.Queue
    with pytest.raises(
        testexceptions.FailedMessageTestError, match="Error: could not load cache"
    ):
        worker(reply_queue, params)  # type: ignore[arg-type]
        watcher_thread.join(timeout=5.0)
        if watcher_thread.is_alive():
            raise testexceptions.WatcherThreadTimeoutError()


@pytest.fixture(name="custom_cmake_command")
def fixture_custom_cmake_command(tmp_path: pathlib.Path) -> pathlib.Path:
    """Fixture generating an executable script to replace CMake."""
    script_path = tmp_path / "custom_cmake.sh"
    with script_path.open("wt", encoding="utf-8") as script_file:
        script_file.write("#!/usr/bin/env bash\n")
        script_file.write("echo 'This is a custom CMake command'\n")
    script_path.chmod(script_path.stat().st_mode | stat.S_IEXEC)
    return script_path


@pytest.mark.xfail(
    CONAN_MAJOR_VERSION == 2,
    reason="CMake build tool command does not exist in Conan 2",
)
def test_cmake_custom_program(
    reply_queue_fixture: typing.Callable[
        [], typing.Tuple[queue.Queue[Message], typing.List[Message], threading.Thread]
    ],
    tmp_path: pathlib.Path,
    caplog: pytest.LogCaptureFixture,
    custom_cmake_command: pathlib.Path,
) -> None:
    """Test: Use a different CMake program."""
    caplog.set_level(logging.INFO)

    worker = workers_api.cmakebuildtool.invoke
    params = CommandParameters("cmakebuild", worker)
    params.cwd = tmp_path
    params.added_environment = {"CONAN_CMAKE_PROGRAM": os.fspath(custom_cmake_command)}
    reply_queue, replies, watcher_thread = reply_queue_fixture()
    # abusing the type system, as the API used for queue.Queue is the same
    # as for multiprocessing.Queue
    worker(reply_queue, params)  # type: ignore[arg-type]
    watcher_thread.join(timeout=5.0)
    if watcher_thread.is_alive():
        raise testexceptions.WatcherThreadTimeoutError()

    assert replies
    assert isinstance(replies[0], Success)
    assert isinstance(replies[0].payload, int)
    assert not replies[0].payload
    assert "This is a custom CMake command" in caplog.text


@pytest.mark.xfail(
    CONAN_MAJOR_VERSION == 2,
    reason="CMake build tool command does not exist in Conan 2",
)
def test_cmake_custom_build_tool(
    reply_queue_fixture: typing.Callable[
        [], typing.Tuple[queue.Queue[Message], typing.List[Message], threading.Thread]
    ],
    tmp_path: pathlib.Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test: Use a custom build tool."""
    caplog.set_level(logging.INFO)

    worker = workers_api.cmakebuildtool.invoke
    params = CommandParameters("cmakebuild", worker)
    params.cwd = tmp_path
    params.added_environment = {"CONAN_MAKE_PROGRAM": "another_make"}
    reply_queue, _, watcher_thread = reply_queue_fixture()
    # abusing the type system, as the API used for queue.Queue is the same
    # as for multiprocessing.Queue
    with pytest.raises(
        testexceptions.FailedMessageTestError, match="Error: could not load cache"
    ):
        worker(reply_queue, params)  # type: ignore[arg-type]
        watcher_thread.join(timeout=5.0)
        if watcher_thread.is_alive():
            raise testexceptions.WatcherThreadTimeoutError()


@pytest.mark.xfail(
    CONAN_MAJOR_VERSION == 2,
    reason="CMake build tool command does not exist in Conan 2",
)
def test_cmake_use_ninja_generator(
    reply_queue_fixture: typing.Callable[
        [], typing.Tuple[queue.Queue[Message], typing.List[Message], threading.Thread]
    ],
    tmp_path: pathlib.Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test: Use the Ninja CMake generator."""
    caplog.set_level(logging.INFO)

    worker = workers_api.cmakebuildtool.invoke
    params = CommandParameters("cmakebuild", worker)
    params.cwd = tmp_path
    params.added_environment = {"CONAN_CMAKE_GENERATOR": "Ninja"}
    reply_queue, _, watcher_thread = reply_queue_fixture()
    # abusing the type system, as the API used for queue.Queue is the same
    # as for multiprocessing.Queue
    with pytest.raises(
        testexceptions.FailedMessageTestError, match="Error: could not load cache"
    ):
        worker(reply_queue, params)  # type: ignore[arg-type]
        watcher_thread.join(timeout=5.0)
        if watcher_thread.is_alive():
            raise testexceptions.WatcherThreadTimeoutError()


@pytest.mark.xfail(
    CONAN_MAJOR_VERSION == 2,
    reason="CMake build tool command does not exist in Conan 2",
)
@pytest.mark.parametrize("generator", [None, "Ninja"])
def test_cmake_verbose_output(
    reply_queue_fixture: typing.Callable[
        [], typing.Tuple[queue.Queue[Message], typing.List[Message], threading.Thread]
    ],
    tmp_path: pathlib.Path,
    caplog: pytest.LogCaptureFixture,
    generator: typing.Optional[str],
) -> None:
    """Test: Generate verbose output from the build tool."""
    caplog.set_level(logging.INFO)

    worker = workers_api.cmakebuildtool.invoke
    params = CommandParameters("cmakebuild", worker)
    params.cwd = tmp_path
    if generator:
        params.added_environment = {"CONAN_CMAKE_GENERATOR": generator}
    params.arguments.append("verbose")
    reply_queue, _, watcher_thread = reply_queue_fixture()
    # abusing the type system, as the API used for queue.Queue is the same
    # as for multiprocessing.Queue
    with pytest.raises(
        testexceptions.FailedMessageTestError, match="Error: could not load cache"
    ):
        worker(reply_queue, params)  # type: ignore[arg-type]
        watcher_thread.join(timeout=5.0)
        if watcher_thread.is_alive():
            raise testexceptions.WatcherThreadTimeoutError()


@pytest.mark.xfail(
    CONAN_MAJOR_VERSION == 2,
    reason="CMake build tool command does not exist in Conan 2",
)
def test_cmake_set_cpu_count(
    reply_queue_fixture: typing.Callable[
        [], typing.Tuple[queue.Queue[Message], typing.List[Message], threading.Thread]
    ],
    tmp_path: pathlib.Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test: Set the CPU count to use."""
    caplog.set_level(logging.INFO)

    worker = workers_api.cmakebuildtool.invoke
    params = CommandParameters("cmakebuild", worker)
    params.cwd = tmp_path
    params.added_environment = {"CONAN_CPU_COUNT": "1"}
    reply_queue, _, watcher_thread = reply_queue_fixture()
    # abusing the type system, as the API used for queue.Queue is the same
    # as for multiprocessing.Queue
    with pytest.raises(
        testexceptions.FailedMessageTestError, match="Error: could not load cache"
    ):
        worker(reply_queue, params)  # type: ignore[arg-type]
        watcher_thread.join(timeout=5.0)
        if watcher_thread.is_alive():
            raise testexceptions.WatcherThreadTimeoutError()
