"""
Test the running an arbitrary conan command, in a single process.

Note that this is not how cruiz tends to work, and should be using multiple processes
to isolate the Conan commands, but this test shows it still works without that
added complexity.
"""

import queue
import threading
import typing
from contextlib import nullcontext as does_not_raise

import cruizlib.workers.api as workers_api
from cruizlib.globals import CONAN_MAJOR_VERSION, CONAN_VERSION_COMPONENTS
from cruizlib.interop.commandparameters import CommandParameters
from cruizlib.interop.message import (
    Message,
    Success,
)

# pylint: disable=wrong-import-order
import pytest

import testexceptions


@pytest.mark.parametrize(
    "verb,args,expectation",
    [
        pytest.param(
            "config",
            ["home"],
            does_not_raise(),
            marks=pytest.mark.xfail(
                CONAN_VERSION_COMPONENTS == (1, 17, 1),
                reason="Conan 1.17.1 does not implement conan config home",
                strict=True,
            ),
        ),
        (
            "config",
            ["unknown"],
            pytest.raises(
                testexceptions.FailedMessageTestError,  # TODO: Check for usage error
            ),
        ),
        (
            "unknown",
            [],
            # TODO: Conan 2 should report "'unknown' is not a Conan command." but is not
            # visible, see https://github.com/markfinal/cruiz/issues/332
            (
                pytest.raises(
                    testexceptions.FailedMessageTestError,
                    match="'Command' object has no attribute 'unknown'",
                )
                if CONAN_MAJOR_VERSION == 1
                else pytest.raises(testexceptions.FailedMessageTestError)
            ),
        ),
    ],
)
def test_arbitrary_conan_command(
    reply_queue_fixture: typing.Callable[
        [], typing.Tuple[queue.Queue[Message], typing.List[Message], threading.Thread]
    ],
    conan_local_cache: typing.Dict[str, str],
    verb: str,
    args: typing.List[str],
    expectation: typing.Iterator[None],
) -> None:
    """
    Test: running arbitrary conan command.

    Uses conan config home as an example.
    """
    worker = workers_api.arbitrary.invoke
    params = CommandParameters(verb, worker)
    params.added_environment = conan_local_cache
    if args:
        params.arguments.extend(args)

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
        assert isinstance(replies[0].payload, str)
        assert replies[0].payload.strip() == str(
            conan_local_cache["_REAL_CONAN_LOCAL_CACHE_DIR"]
        )
