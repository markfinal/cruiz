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
from cruizlib.globals import CONAN_MAJOR_VERSION
from cruizlib.interop.commandparameters import CommandParameters
from cruizlib.interop.message import (
    Message,
    Success,
)

# pylint: disable=wrong-import-order
import pytest

# pylint: disable=import-error
import testexceptions


LOGGER = logging.getLogger(__name__)


def test_expected_failure(
    reply_queue_fixture: typing.Tuple[
        queue.Queue[Message], typing.List[Message], threading.Thread
    ],
) -> None:
    """Test: running conan install incorrect setup, so has an expected failure."""
    worker = workers_api.install.invoke
    params = CommandParameters("install", worker)
    reply_queue, _, watcher_thread = reply_queue_fixture
    # abusing the type system, as the API used for queue.Queue is the same
    # as for multiprocessing.Queue
    worker(reply_queue, params)  # type: ignore[arg-type]
    with pytest.raises(testexceptions.FailedMessageTestError):
        watcher_thread.join()


def test_conan_install(
    reply_queue_fixture: typing.Tuple[
        queue.Queue[Message], typing.List[Message], threading.Thread
    ],
    conan_recipe: pathlib.Path,
) -> None:
    """Test: running conan install."""
    worker = workers_api.install.invoke
    params = CommandParameters("install", worker)
    params.recipe_path = conan_recipe
    params.cwd = conan_recipe.parent
    params.profile = "default"
    reply_queue, replies, watcher_thread = reply_queue_fixture
    # abusing the type system, as the API used for queue.Queue is the same
    # as for multiprocessing.Queue
    worker(reply_queue, params)  # type: ignore[arg-type]
    watcher_thread.join()

    assert replies
    assert isinstance(replies[0], Success)
    if CONAN_MAJOR_VERSION == 1:
        assert (conan_recipe.parent / "conan.lock").exists()
