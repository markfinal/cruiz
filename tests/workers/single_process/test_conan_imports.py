"""
Test the conan imports functionality, in a single process.

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

import testexceptions


LOGGER = logging.getLogger(__name__)


@pytest.mark.xfail(
    CONAN_MAJOR_VERSION == 2,
    reason="conan imports command does not exist in Conan 2",
    strict=True,
)
@pytest.mark.parametrize(
    "arg,value",
    [
        (None, None),
        ("install_folder", "install"),
        ("imports_folder", "imports"),
    ],
)
# pylint: disable=too-many-arguments, too-many-positional-arguments
def test_conan_imports(
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
    Test: running conan imports.

    A prerequisite is to run conan install first.

    Note I couldn't get imports to fail, when the 'install' folders differed.
    """
    worker = workers_api.install.invoke
    params = CommandParameters("install", worker)
    params.added_environment = conan_local_cache
    params.recipe_path = conan_recipe
    params.cwd = conan_recipe.parent
    params.profile = "default"
    if arg and isinstance(arg, str) and arg == "install_folder":
        assert isinstance(value, str)
        params.install_folder = tmp_path / value
    reply_queue, replies, watcher_thread = reply_queue_fixture()
    # abusing the type system, as the API used for queue.Queue is the same
    # as for multiprocessing.Queue
    worker(reply_queue, params)  # type: ignore[arg-type]
    watcher_thread.join(timeout=5.0)
    if watcher_thread.is_alive():
        raise testexceptions.WatcherThreadTimeoutError()

    worker = workers_api.imports.invoke
    params = CommandParameters("imports", worker)
    params.added_environment = conan_local_cache
    params.recipe_path = conan_recipe
    params.cwd = conan_recipe.parent
    if arg:
        if arg == "install_folder":
            assert isinstance(value, str)
            params.install_folder = tmp_path / value
        elif arg == "imports_folder":
            assert isinstance(value, str)
            params.imports_folder = tmp_path / value
    reply_queue, replies, watcher_thread = reply_queue_fixture()
    # abusing the type system, as the API used for queue.Queue is the same
    # as for multiprocessing.Queue
    worker(reply_queue, params)  # type: ignore[arg-type]
    watcher_thread.join(timeout=5.0)
    if watcher_thread.is_alive():
        raise testexceptions.WatcherThreadTimeoutError()

    assert replies
    assert isinstance(replies[0], Success)
