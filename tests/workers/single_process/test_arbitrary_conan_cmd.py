"""
Test the running an arbitrary conan command, in a single process.

Note that this is not how cruiz tends to work, and should be using multiple processes
to isolate the Conan commands, but this test shows it still works without that
added complexity.
"""

from __future__ import annotations

import typing
from contextlib import nullcontext as does_not_raise

import cruizlib.workers.api as workers_api
from cruizlib.globals import CONAN_MAJOR_VERSION, CONAN_VERSION_COMPONENTS
from cruizlib.interop.commandparameters import CommandParameters
from cruizlib.interop.message import Success

# pylint: disable=wrong-import-order
import pytest

import texceptions

if typing.TYPE_CHECKING:
    from ttypes import RunWorkerFixture, SingleprocessReplyQueueFixture


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
                texceptions.FailedMessageTestError,  # TODO: Check for usage error
            ),
        ),
        (
            "unknown",
            [],
            # TODO: Conan 2 should report "'unknown' is not a Conan command." but is not
            # visible, see https://github.com/markfinal/cruiz/issues/332
            (
                pytest.raises(
                    texceptions.FailedMessageTestError,
                    match="'Command' object has no attribute 'unknown'",
                )
                if CONAN_MAJOR_VERSION == 1
                else pytest.raises(texceptions.FailedMessageTestError)
            ),
        ),
    ],
)
# pylint: disable=too-many-arguments, too-many-positional-arguments
def test_arbitrary_conan_command(
    reply_queue_fixture: SingleprocessReplyQueueFixture,
    run_worker: RunWorkerFixture,
    conan_local_cache: typing.Dict[str, str],
    verb: str,
    args: typing.List[str],
    expectation: typing.ContextManager[None],
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

    reply_queue, replies, watcher_thread, context = reply_queue_fixture()
    with expectation:
        run_worker(worker, reply_queue, params, watcher_thread, context)

        assert replies
        assert isinstance(replies[0], Success)
        assert isinstance(replies[0].payload, str)
        assert replies[0].payload.strip() == str(
            conan_local_cache["_REAL_CONAN_LOCAL_CACHE_DIR"]
        )
