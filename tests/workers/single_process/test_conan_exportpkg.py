"""
Test the conan export-pkg functionality, in a single process.

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
from cruizlib.globals import CONAN_MAJOR_VERSION, CONAN_VERSION_COMPONENTS
from cruizlib.interop.commandparameters import CommandParameters
from cruizlib.interop.message import (
    Message,
    Success,
)

# pylint: disable=wrong-import-order
import pytest

import texceptions


LOGGER = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "arg,value",
    [
        (None, None),
        ("version", "conan_recipe_version"),
        ("install_folder", "install"),
        ("source_folder", "source"),
        ("build_folder", "build"),
        ("package_folder", "package"),
        (("user", "channel"), ("user1", "channel1")),
    ],
)
# pylint: disable=too-many-arguments, too-many-positional-arguments, too-many-branches, too-many-locals, too-many-statements  # noqa: E501
def test_conan_exportpkg(
    reply_queue_fixture: typing.Callable[
        [], typing.Tuple[queue.Queue[Message], typing.List[Message], threading.Thread]
    ],
    conan_recipe_name: str,
    conan_recipe: pathlib.Path,
    conan_local_cache: typing.Dict[str, str],
    tmp_path: pathlib.Path,
    arg: typing.Optional[str],
    value: typing.Union[typing.Optional[str], typing.List[str], typing.Dict[str, str]],
    request: pytest.FixtureRequest,
) -> None:
    """
    Test: running conan export-pkg.

    conan install is a required prerequisite, IF the install folder is specified.
    """
    if arg and arg == "install_folder":
        worker = workers_api.install.invoke
        params = CommandParameters("install", worker)
        params.added_environment = conan_local_cache
        params.recipe_path = conan_recipe
        params.cwd = conan_recipe.parent
        params.profile = "default"
        if arg and isinstance(arg, str) and arg == "install_folder":
            assert isinstance(value, str)
            params.install_folder = tmp_path / value
        if CONAN_VERSION_COMPONENTS == (1, 17, 1):
            # since this early Conan version requires a user and channel on pkgrefs
            params.user = params.user or "test_user"
            params.channel = params.channel or "test_channel"
        reply_queue, replies, watcher_thread = reply_queue_fixture()
        # abusing the type system, as the API used for queue.Queue is the same
        # as for multiprocessing.Queue
        worker(reply_queue, params)  # type: ignore[arg-type]
        watcher_thread.join(timeout=5.0)
        if watcher_thread.is_alive():
            raise texceptions.WatcherThreadTimeoutError()

    worker = workers_api.exportpackage.invoke
    params = CommandParameters("export-pkg", worker)
    params.added_environment = conan_local_cache
    params.recipe_path = conan_recipe
    params.cwd = conan_recipe.parent
    params.name = conan_recipe_name
    if CONAN_VERSION_COMPONENTS == (1, 17, 1):
        # since this early Conan version requires a user and channel on pkgrefs
        params.user = params.user or "test_user"
        params.channel = params.channel or "test_channel"
    if arg:
        if isinstance(arg, str):
            if arg == "install_folder":
                assert isinstance(value, str)
                params.install_folder = tmp_path / value
            elif arg == "source_folder":
                assert isinstance(value, str)
                params.source_folder = tmp_path / value
                # conan checks if the folder exists
                params.source_folder.mkdir(parents=True)
            elif arg == "build_folder":
                assert isinstance(value, str)
                params.build_folder = tmp_path / value
                # conan checks if the folder exists
                params.build_folder.mkdir(parents=True)
            elif arg == "package_folder":
                assert isinstance(value, str)
                params.package_folder = tmp_path / value
                # conan checks if the folder exists
                params.package_folder.mkdir(parents=True)
            elif arg == "force":
                assert isinstance(value, bool)
                params.force = value
            else:
                assert isinstance(value, str)
                try:
                    true_value = request.getfixturevalue(value)
                except pytest.FixtureLookupError:
                    true_value = value
                setattr(params, arg, true_value)
        else:
            assert isinstance(arg, tuple)
            for index, key in enumerate(arg):
                setattr(params, key, value[index])
    reply_queue, replies, watcher_thread = reply_queue_fixture()
    # abusing the type system, as the API used for queue.Queue is the same
    # as for multiprocessing.Queue
    worker(reply_queue, params)  # type: ignore[arg-type]
    watcher_thread.join(timeout=5.0)
    if watcher_thread.is_alive():
        raise texceptions.WatcherThreadTimeoutError()

    assert replies
    assert isinstance(replies[0], Success)

    if CONAN_MAJOR_VERSION == 1:
        # repeat the export to fail, because it requires a force
        reply_queue, replies, watcher_thread = reply_queue_fixture()
        # abusing the type system, as the API used for queue.Queue is the same
        # as for multiprocessing.Queue
        with pytest.raises(texceptions.FailedMessageTestError) as exc:
            worker(reply_queue, params)  # type: ignore[arg-type]
            watcher_thread.join(timeout=5.0)
            if watcher_thread.is_alive():
                raise texceptions.WatcherThreadTimeoutError()

        assert "Package already exists" in str(exc.value)

        # repeat the export with a force, to succeed
        params.force = True
    else:
        # Conan 2 does not fail to re-export, not need a force
        pass

    reply_queue, replies, watcher_thread = reply_queue_fixture()
    # abusing the type system, as the API used for queue.Queue is the same
    # as for multiprocessing.Queue
    worker(reply_queue, params)  # type: ignore[arg-type]
    watcher_thread.join(timeout=5.0)
    if watcher_thread.is_alive():
        raise texceptions.WatcherThreadTimeoutError()

    assert replies
    assert isinstance(replies[0], Success)
