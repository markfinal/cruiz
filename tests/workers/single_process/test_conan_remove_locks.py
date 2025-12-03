"""
Test the conan remove locks functionality, in a single process.

Note that this is not how cruiz tends to work, and should be using multiple processes
to isolate the Conan commands, but this test shows it still works without that
added complexity.
"""

from __future__ import annotations

import logging
import typing

import cruizlib.workers.api as workers_api
from cruizlib.globals import CONAN_MAJOR_VERSION
from cruizlib.interop.commandparameters import CommandParameters
from cruizlib.interop.message import Success

# pylint: disable=wrong-import-order
import pytest

if typing.TYPE_CHECKING:
    from ttypes import MultiprocessReplyQueueFixture, RunWorkerFixture


LOGGER = logging.getLogger(__name__)


@pytest.mark.xfail(
    CONAN_MAJOR_VERSION == 2,
    reason="Remove locks does not exist in Conan 2",
    strict=True,
)
def test_conan_remove_locks(
    multiprocess_reply_queue_fixture: MultiprocessReplyQueueFixture,
    run_worker: RunWorkerFixture,
    conan_local_cache: typing.Dict[str, str],
) -> None:
    """Test: running conan remove locks."""
    worker = workers_api.removelocks.invoke
    params = CommandParameters("removelocks", worker)
    params.added_environment = conan_local_cache
    reply_queue, replies, watcher_thread, context = multiprocess_reply_queue_fixture()
    run_worker(worker, reply_queue, params, watcher_thread, context)

    assert replies
    assert isinstance(replies[0], Success)
    assert replies[0].payload is None
