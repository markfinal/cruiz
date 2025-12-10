"""
Test the conan remove (all packages) functionality, in a single process.

Note that this is not how cruiz tends to work, and should be using multiple processes
to isolate the Conan commands, but this test shows it still works without that
added complexity.
"""

from __future__ import annotations

import logging
import pathlib
import typing

import cruizlib.workers.api as workers_api
from cruizlib.globals import CONAN_VERSION_COMPONENTS
from cruizlib.interop.commandparameters import CommandParameters
from cruizlib.interop.message import Success

if typing.TYPE_CHECKING:
    from ttypes import RunWorkerFixture, SingleprocessReplyQueueFixture


LOGGER = logging.getLogger(__name__)


def test_conan_remove_all_packages(
    reply_queue_fixture: SingleprocessReplyQueueFixture,
    run_worker: RunWorkerFixture,
    conan_local_cache: typing.Dict[str, str],
    conan_recipe: pathlib.Path,
) -> None:
    """
    Test: running conan remove (for all packages).

    Requires installing a package first.
    """
    worker = workers_api.create.invoke
    params = CommandParameters("create", worker)
    params.added_environment = conan_local_cache
    params.recipe_path = conan_recipe
    params.cwd = conan_recipe.parent
    params.profile = "default"
    if CONAN_VERSION_COMPONENTS == (1, 17, 1):
        params.user = "user1"
        params.channel = "channel1"
    reply_queue, replies, watcher_thread, context = reply_queue_fixture()
    run_worker(worker, reply_queue, params, watcher_thread, context)

    worker = workers_api.removeallpackages.invoke
    params = CommandParameters("removeallpackages", worker)
    params.added_environment = conan_local_cache
    reply_queue, replies, watcher_thread, context = reply_queue_fixture()
    run_worker(worker, reply_queue, params, watcher_thread, context)

    assert replies
    assert isinstance(replies[0], Success)
    assert isinstance(replies[0].payload, bool)
    assert replies[0].payload
