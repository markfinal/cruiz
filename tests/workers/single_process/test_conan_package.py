"""
Test the conan package functionality, in a single process.

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


@pytest.mark.skipif(
    CONAN_MAJOR_VERSION == 2, reason="Conan 2 does not have a package command"
)
@pytest.mark.parametrize(
    "arg,value",
    [
        (None, None),
        ("install_folder", "install"),
        ("source_folder", "src"),
        ("build_folder", "buils"),
        ("package_folder", "package"),
    ],
)
# pylint: disable=too-many-arguments, too-many-positional-arguments, too-many-branches, too-many-locals, too-many-statements  # noqa: E501
def test_conan_package(
    reply_queue_fixture: typing.Callable[
        [], typing.Tuple[queue.Queue[Message], typing.List[Message], threading.Thread]
    ],
    conan_recipe: pathlib.Path,
    conan_local_cache: typing.Dict[str, str],
    tmp_path: pathlib.Path,
    arg: typing.Optional[str],
    value: typing.Union[typing.Optional[str], typing.List[str], typing.Dict[str, str]],
) -> None:
    """
    Test: running conan package.

    This is a Conan 1 only command.

    conan install is a required prerequisite.
    """
    worker = workers_api.install.invoke
    params = CommandParameters("install", worker)
    params.added_environment = conan_local_cache
    params.recipe_path = conan_recipe
    params.cwd = conan_recipe.parent
    params.profile = "default"
    if arg and isinstance(arg, str) and arg in ("install_folder", "build_folder"):
        # if specifying build_folder, this changes the behaviour of looking
        # in the cwd for the install artifacts
        assert isinstance(value, str)
        params.install_folder = tmp_path / value
    reply_queue, replies, watcher_thread = reply_queue_fixture()
    # abusing the type system, as the API used for queue.Queue is the same
    # as for multiprocessing.Queue
    worker(reply_queue, params)  # type: ignore[arg-type]
    watcher_thread.join(timeout=5.0)
    if watcher_thread.is_alive():
        raise testexceptions.WatcherThreadTimeoutError()

    worker = workers_api.package.invoke
    params = CommandParameters("package", worker)
    params.added_environment = conan_local_cache
    params.recipe_path = conan_recipe
    params.cwd = conan_recipe.parent
    if arg:
        if arg == "install_folder":
            assert isinstance(value, str)
            params.install_folder = tmp_path / value
        elif arg == "source_folder":
            assert isinstance(value, str)
            params.source_folder = tmp_path / value
        elif arg == "build_folder":
            assert isinstance(value, str)
            params.build_folder = tmp_path / value
        elif arg == "package_folder":
            assert isinstance(value, str)
            params.package_folder = tmp_path / value
    reply_queue, replies, watcher_thread = reply_queue_fixture()
    # abusing the type system, as the API used for queue.Queue is the same
    # as for multiprocessing.Queue
    worker(reply_queue, params)  # type: ignore[arg-type]
    watcher_thread.join(timeout=5.0)
    if watcher_thread.is_alive():
        raise testexceptions.WatcherThreadTimeoutError()

    assert replies
    assert isinstance(replies[0], Success)
