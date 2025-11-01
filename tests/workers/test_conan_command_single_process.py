"""
Test the Conan command functionality, in a single process.

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
from cruizlib.interop.commandparameters import CommandParameters
from cruizlib.interop.message import (
    Failure,
    Message,
    Success,
)


LOGGER = logging.getLogger(__name__)


def test_expected_failure(
    reply_queue_fixture: typing.Tuple[
        queue.Queue[Message], typing.List[Message], threading.Thread
    ],
) -> None:
    """Test: running conan install incorrect setup, so has an expected failure."""
    worker = workers_api.install.invoke
    params = CommandParameters("install", worker)
    reply_queue, replies, watcher_thread = reply_queue_fixture
    # abusing the type system, as the API used for queue.Queue is the same
    # as for multiprocessing.Queue
    worker(reply_queue, params)  # type: ignore[arg-type]
    watcher_thread.join()

    assert replies
    assert isinstance(replies[0], Failure)


def test_conan_install(
    reply_queue_fixture: typing.Tuple[
        queue.Queue[Message], typing.List[Message], threading.Thread
    ],
    conan1_recipe: pathlib.Path,
) -> None:
    """Test: running conan install."""
    worker = workers_api.install.invoke
    params = CommandParameters("install", worker)
    params.recipe_path = conan1_recipe
    params.cwd = conan1_recipe.parent
    params.profile = "default"
    reply_queue, replies, watcher_thread = reply_queue_fixture
    # abusing the type system, as the API used for queue.Queue is the same
    # as for multiprocessing.Queue
    worker(reply_queue, params)  # type: ignore[arg-type]
    watcher_thread.join()

    assert replies
    assert isinstance(replies[0], Success)
    assert (conan1_recipe.parent / "conan.lock").exists()
