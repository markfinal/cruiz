"""
Test the conan remote package revisions search functionality, in a single process.

Note that this is not how cruiz tends to work, and should be using multiple processes
to isolate the Conan commands, but this test shows it still works without that
added complexity.
"""

import logging
import queue
import threading
import typing
from contextlib import nullcontext as does_not_raise


import cruizlib.workers.api as workers_api
from cruizlib.globals import CONAN_MAJOR_VERSION, CONAN_VERSION_COMPONENTS
from cruizlib.interop.message import (
    Message,
    Success,
)
from cruizlib.interop.packagerevisionsparameters import PackageRevisionsParameters

# pylint: disable=wrong-import-order
import pytest

import testexceptions


LOGGER = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "envvars,expectation",
    [
        pytest.param(
            {"CONAN_REVISIONS_ENABLED": "0"},
            pytest.raises(testexceptions.FailedMessageTestError),
            marks=pytest.mark.xfail(
                CONAN_MAJOR_VERSION == 2,
                reason="Conan 2 does not allow disabling revisions",
            ),
        ),
        pytest.param(
            {"CONAN_REVISIONS_ENABLED": "1"},
            does_not_raise(),
            marks=pytest.mark.xfail(
                CONAN_VERSION_COMPONENTS == (1, 17, 1),
                reason="Conan 1.17.1 cannot connect",
            ),
        ),
    ],
)
def test_conan_remote_prev_search(
    reply_queue_fixture: typing.Callable[
        [], typing.Tuple[queue.Queue[Message], typing.List[Message], threading.Thread]
    ],
    conan_local_cache: typing.Dict[str, str],
    envvars: typing.Dict[str, str],
    expectation: typing.Iterator[None],
) -> None:
    """
    Test: running conan remote package revisions searches for a given package.

    The zlib rrev and package_id are real values from Conan Center.
    """
    worker = workers_api.packagerevisions.invoke
    rrev = "f52e03ae3d251dec704634230cd806a2"
    if CONAN_MAJOR_VERSION == 1:
        package_id = "0508f825aee0fe3099a5dae626a5316104c6db0a"
    else:
        package_id = "d62dff20d86436b9c58ddc0162499d197be9de1e"
    params = PackageRevisionsParameters(
        reference=f"zlib/1.3.1#{rrev}:{package_id}",
        remote_name="conancenter",
    )
    params.added_environment = conan_local_cache
    params.added_environment.update(envvars)
    reply_queue, replies, watcher_thread = reply_queue_fixture()
    # abusing the type system, as the API used for queue.Queue is the same
    # as for multiprocessing.Queue
    with expectation:  # type: ignore[attr-defined]
        worker(reply_queue, params)  # type: ignore[arg-type]
        watcher_thread.join(timeout=5.0)
        if watcher_thread.is_alive():
            raise testexceptions.WatcherThreadTimeoutError()

        assert replies
        assert isinstance(replies[0], Success)
        assert isinstance(replies[0].payload, list)
        assert replies[0].payload
        assert "revision" in replies[0].payload[0]
        assert "time" in replies[0].payload[0]
