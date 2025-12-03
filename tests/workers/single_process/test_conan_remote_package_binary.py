"""
Test the conan remote package binary download functionality, in a single process.

Note that this is not how cruiz tends to work, and should be using multiple processes
to isolate the Conan commands, but this test shows it still works without that
added complexity.
"""

import logging
import pathlib
import queue
import threading
import typing


import cruizlib.workers.api as workers_api
from cruizlib.globals import CONAN_MAJOR_VERSION, CONAN_VERSION_COMPONENTS
from cruizlib.interop.message import (
    Message,
    Success,
)
from cruizlib.interop.packagebinaryparameters import PackageBinaryParameters

# pylint: disable=wrong-import-order
import pytest

import texceptions


LOGGER = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "envvars",
    [
        pytest.param(
            {"CONAN_REVISIONS_ENABLED": "0"},
            marks=pytest.mark.xfail(
                CONAN_VERSION_COMPONENTS == (1, 17, 1),
                reason="Conan 1.17.1 requires user and channel",
                strict=True,
            ),
        ),
        pytest.param(
            {"CONAN_REVISIONS_ENABLED": "1"},
            marks=pytest.mark.xfail(
                CONAN_VERSION_COMPONENTS == (1, 17, 1),
                reason="Conan 1.17.1 cannot connect",
                strict=True,
            ),
        ),
    ],
)
def test_conan_remote_package_binary_download(
    reply_queue_fixture: typing.Callable[
        [], typing.Tuple[queue.Queue[Message], typing.List[Message], threading.Thread]
    ],
    conan_local_cache: typing.Dict[str, str],
    envvars: typing.Dict[str, str],
    tmp_path: pathlib.Path,
) -> None:
    """Test: downloading specific package binaries."""
    worker = workers_api.packagebinary.invoke
    rrev = "f52e03ae3d251dec704634230cd806a2"
    if CONAN_MAJOR_VERSION == 1:
        package_id = "0508f825aee0fe3099a5dae626a5316104c6db0a"
        prev = "199228d574b71c0c6428ebbbbc3d2a0e"
    else:
        package_id = "d62dff20d86436b9c58ddc0162499d197be9de1e"
        prev = "c4506d0ca4188035101e46f9b99cc29f"
    params = PackageBinaryParameters(
        reference=f"zlib/1.3.1#{rrev}:{package_id}#{prev}",
        remote_name="conancenter",
        where=tmp_path,
    )
    params.added_environment = conan_local_cache
    params.added_environment.update(envvars)
    reply_queue, replies, watcher_thread = reply_queue_fixture()
    # abusing the type system, as the API used for queue.Queue is the same
    # as for multiprocessing.Queue
    worker(reply_queue, params)  # type: ignore[arg-type]
    watcher_thread.join(timeout=5.0)
    if watcher_thread.is_alive():
        raise texceptions.WatcherThreadTimeoutError()

    assert replies
    assert isinstance(replies[0], Success)
    if CONAN_MAJOR_VERSION == 1:
        if envvars["CONAN_REVISIONS_ENABLED"] == "0":
            assert isinstance(replies[0].payload, dict)
        else:
            assert isinstance(replies[0].payload, list)
    else:
        assert isinstance(replies[0].payload, dict)
    assert "conaninfo.txt" in replies[0].payload
    assert "conan_package.tgz" in replies[0].payload
    assert "conanmanifest.txt" in replies[0].payload
