"""
Test the conan remote package_id search functionality, in a single process.

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
from cruizlib.interop.packageidparameters import PackageIdParameters

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
def test_conan_remote_package_id_search(
    reply_queue_fixture: typing.Callable[
        [], typing.Tuple[queue.Queue[Message], typing.List[Message], threading.Thread]
    ],
    conan_local_cache: typing.Dict[str, str],
    envvars: typing.Dict[str, str],
    expectation: typing.Iterator[None],
) -> None:
    """Test: running conan remote pacage_id searches for a given package."""
    worker = workers_api.packagedetails.invoke
    params = PackageIdParameters(
        reference="zlib/1.3.1#f52e03ae3d251dec704634230cd806a2",
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
        assert "id" in replies[0].payload[0]
        assert "options" in replies[0].payload[0]
        assert "settings" in replies[0].payload[0]
        if CONAN_MAJOR_VERSION == 1:
            assert "requires" in replies[0].payload[0]
        else:
            # I suspect Conan 2 trims empty lists as zlib has no dependencies
            pass
