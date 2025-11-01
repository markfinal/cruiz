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


@pytest.mark.parametrize(
    "arg,value",
    [
        (None, None),
        ("version", "1.0"),
        ("install_folder", "install"),
        ("options", {"shared": "True"}),
        (("user", "channel"), ("user1", "channel1")),
        # (conan2) conan install <path> works but conan install --update <path>
        # defaults to the current directory - there is documentation saying this
        # happens, but not for adding --update
        pytest.param(
            "arguments",
            ["--update"],
            marks=pytest.mark.xfail(
                CONAN_MAJOR_VERSION == 2,
                reason="Unexpected Conan 2 install behaviour with --update",
            ),
        ),
    ],
)
# pylint: disable=too-many-arguments, too-many-positional-arguments
def test_conan_install(
    reply_queue_fixture: typing.Tuple[
        queue.Queue[Message], typing.List[Message], threading.Thread
    ],
    conan_recipe: pathlib.Path,
    conan_local_cache: typing.Dict[str, str],
    tmp_path: pathlib.Path,
    arg: typing.Optional[str],
    value: typing.Union[typing.Optional[str], typing.List[str], typing.Dict[str, str]],
) -> None:
    """Test: running conan install."""
    worker = workers_api.install.invoke
    params = CommandParameters("install", worker)
    params.added_environment = conan_local_cache
    params.recipe_path = conan_recipe
    params.cwd = conan_recipe.parent
    params.profile = "default"
    if arg:
        if isinstance(arg, str):
            if arg == "arguments":
                assert isinstance(value, list)
                params.arguments.extend(value)
            elif arg == "options":
                assert isinstance(value, dict)
                for key, val in value.items():
                    params.add_option("test", key, val)
            elif arg == "install_folder":
                assert isinstance(value, str)
                params.install_folder = tmp_path / value
            else:
                setattr(params, arg, value)
        else:
            assert isinstance(arg, tuple)
            for index, key in enumerate(arg):
                setattr(params, key, value[index])
    reply_queue, replies, watcher_thread = reply_queue_fixture
    # abusing the type system, as the API used for queue.Queue is the same
    # as for multiprocessing.Queue
    worker(reply_queue, params)  # type: ignore[arg-type]
    watcher_thread.join()

    assert replies
    assert isinstance(replies[0], Success)
    if CONAN_MAJOR_VERSION == 1:
        if arg == "install_folder":
            assert isinstance(value, str)
            assert (tmp_path / value / "conan.lock").exists()
        else:
            assert (conan_recipe.parent / "conan.lock").exists()
