"""
Test the conan remote search functionality, in a single process.

Note that this is not how cruiz tends to work, and should be using multiple processes
to isolate the Conan commands, but this test shows it still works without that
added complexity.
"""

import logging
import queue
import threading
import typing


import cruizlib.workers.api as workers_api
from cruizlib.globals import CONAN_MAJOR_VERSION, CONAN_VERSION_COMPONENTS
from cruizlib.interop.message import (
    Message,
    Success,
)
from cruizlib.interop.searchrecipesparameters import SearchRecipesParameters

# pylint: disable=wrong-import-order
import pytest

import testexceptions


LOGGER = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "aliasaware",
    [
        False,
        pytest.param(
            True,
            marks=pytest.mark.skipif(
                CONAN_MAJOR_VERSION == 2, reason="Conan 2 does not recommend alises"
            ),
        ),
    ],
)
def test_conan_remote_search_pkg_exists(
    reply_queue_fixture: typing.Callable[
        [], typing.Tuple[queue.Queue[Message], typing.List[Message], threading.Thread]
    ],
    conan_local_cache: typing.Dict[str, str],
    aliasaware: bool,
) -> None:
    """Test: running conan remote searches for a package that will exist."""
    worker = workers_api.remotesearch.invoke
    params = SearchRecipesParameters(
        remote_name="conancenter",
        alias_aware=aliasaware,
        case_sensitive=True,
        pattern="zlib",
    )
    params.added_environment = conan_local_cache
    reply_queue, replies, watcher_thread = reply_queue_fixture()
    # abusing the type system, as the API used for queue.Queue is the same
    # as for multiprocessing.Queue
    if CONAN_VERSION_COMPONENTS == (1, 17, 1):
        with pytest.raises(testexceptions.FailedMessageTestError) as exc_info:
            worker(reply_queue, params)  # type: ignore[arg-type]
            watcher_thread.join(timeout=5.0)
            if watcher_thread.is_alive():
                raise testexceptions.WatcherThreadTimeoutError()
        assert exc_info.value.exception_type_name == "ConanConnectionError"
    else:
        worker(reply_queue, params)  # type: ignore[arg-type]
        watcher_thread.join(timeout=5.0)
        if watcher_thread.is_alive():
            raise testexceptions.WatcherThreadTimeoutError()

        assert replies
        assert isinstance(replies[0], Success)
        assert isinstance(replies[0].payload, list)
        assert replies[0].payload
        assert isinstance(replies[0].payload[0], tuple)
        assert isinstance(replies[0].payload[0][0], str)
        assert replies[0].payload[0][1] is None, "No alias expected"


def test_conan_remote_search_pkg_not_exists(
    reply_queue_fixture: typing.Callable[
        [], typing.Tuple[queue.Queue[Message], typing.List[Message], threading.Thread]
    ],
    conan_local_cache: typing.Dict[str, str],
) -> None:
    """Test: running conan remote searches for a package that will not exist."""
    worker = workers_api.remotesearch.invoke
    params = SearchRecipesParameters(
        remote_name="conancenter",
        alias_aware=False,
        case_sensitive=True,
        pattern="doesnotexist",
    )
    params.added_environment = conan_local_cache
    reply_queue, replies, watcher_thread = reply_queue_fixture()
    # abusing the type system, as the API used for queue.Queue is the same
    # as for multiprocessing.Queue
    if CONAN_VERSION_COMPONENTS == (1, 17, 1):
        with pytest.raises(testexceptions.FailedMessageTestError) as exc_info:
            worker(reply_queue, params)  # type: ignore[arg-type]
            watcher_thread.join(timeout=5.0)
            if watcher_thread.is_alive():
                raise testexceptions.WatcherThreadTimeoutError()
        assert exc_info.value.exception_type_name == "ConanConnectionError"
    elif CONAN_MAJOR_VERSION == 1:
        worker(reply_queue, params)  # type: ignore[arg-type]
        watcher_thread.join(timeout=5.0)
        if watcher_thread.is_alive():
            raise testexceptions.WatcherThreadTimeoutError()

        assert replies
        assert isinstance(replies[0], Success)
        assert replies[0].payload is None
    else:
        with pytest.raises(testexceptions.FailedMessageTestError) as exc_info:
            worker(reply_queue, params)  # type: ignore[arg-type]
            watcher_thread.join(timeout=5.0)
            if watcher_thread.is_alive():
                raise testexceptions.WatcherThreadTimeoutError()
        if CONAN_VERSION_COMPONENTS == (2, 0, 14):
            assert exc_info.value.exception_type_name == "ConanException"
        else:
            assert exc_info.value.exception_type_name == "NotFoundException"
        assert str(exc_info.value).startswith("(\"Recipe 'doesnotexist' not found")
