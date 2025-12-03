"""
Test the conan AutoToolsBuildEnvironment 1 helper functionality, in a single process.

Note that this is not how cruiz tends to work, and should be using multiple processes
to isolate the Conan commands, but this test shows it still works without that
added complexity.
"""

import logging
import os
import pathlib
import queue
import threading
import typing

import cruizlib.workers.api as workers_api
from cruizlib.constants import BuildFeatureConstants
from cruizlib.globals import CONAN_MAJOR_VERSION
from cruizlib.interop.commandparameters import CommandParameters
from cruizlib.interop.message import (
    Message,
    Success,
)

# pylint: disable=wrong-import-order
import pytest

import texceptions


LOGGER = logging.getLogger(__name__)


@pytest.mark.skipif(
    CONAN_MAJOR_VERSION == 2, reason="Conan 2 does not support this AutoTools helper."
)
@pytest.mark.parametrize(
    "env_key,env_value",
    [
        (None, None),
        (
            (
                BuildFeatureConstants.CCACHEEXECUTABLE.name,
                BuildFeatureConstants.CCACHEAUTOTOOLSCONFIGARGS.name,
            ),
            ("ccache", "-v"),
        ),
        (
            (
                BuildFeatureConstants.SCCACHEEXECUTABLE.name,
                BuildFeatureConstants.SCCACHEAUTOTOOLSCONFIGARGS.name,
            ),
            ("sccache", "-v"),
        ),
        (
            (
                BuildFeatureConstants.BUILDCACHEEXECUTABLE.name,
                BuildFeatureConstants.BUILDCACHEAUTOTOOLSCONFIGARGS.name,
            ),
            ("buildcache", "-v"),
        ),
    ],
)
# pylint: disable=too-many-arguments, too-many-positional-arguments  # noqa: E501
def test_conan_autotoolsbuildhelper_configure(
    reply_queue_fixture: typing.Callable[
        [], typing.Tuple[queue.Queue[Message], typing.List[Message], threading.Thread]
    ],
    conan_autotoolsbuildenvironment_configure_recipe: pathlib.Path,
    conan_local_cache: typing.Dict[str, str],
    _configure_script: pathlib.Path,
    env_key: typing.Optional[str],
    env_value: typing.Optional[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Test: running the AutoToolsBuildEnvironment helper configure method.

    conan install is a required prerequisite.
    """
    if CONAN_MAJOR_VERSION == 1:
        worker = workers_api.install.invoke
        params = CommandParameters("install", worker)
        params.added_environment = conan_local_cache
        params.recipe_path = conan_autotoolsbuildenvironment_configure_recipe
        params.cwd = conan_autotoolsbuildenvironment_configure_recipe.parent
        params.profile = "default"
        reply_queue, replies, watcher_thread = reply_queue_fixture()
        # abusing the type system, as the API used for queue.Queue is the same
        # as for multiprocessing.Queue
        worker(reply_queue, params)  # type: ignore[arg-type]
        watcher_thread.join(timeout=5.0)
        if watcher_thread.is_alive():
            raise texceptions.WatcherThreadTimeoutError()

    if env_key and env_value:
        for key, value in zip(env_key, env_value):
            monkeypatch.setenv(key, value)

    worker = workers_api.build.invoke
    params = CommandParameters("build", worker)
    params.added_environment = conan_local_cache
    params.recipe_path = conan_autotoolsbuildenvironment_configure_recipe
    params.cwd = conan_autotoolsbuildenvironment_configure_recipe.parent
    reply_queue, replies, watcher_thread = reply_queue_fixture()
    # abusing the type system, as the API used for queue.Queue is the same
    # as for multiprocessing.Queue
    worker(reply_queue, params)  # type: ignore[arg-type]
    watcher_thread.join(timeout=5.0)
    if watcher_thread.is_alive():
        raise texceptions.WatcherThreadTimeoutError()

    assert replies
    assert isinstance(replies[0], Success)


@pytest.mark.skipif(
    CONAN_MAJOR_VERSION == 2, reason="Conan 2 does not support this AutoTools helper."
)
@pytest.mark.parametrize(
    "env_key,env_value",
    [
        (None, None),
        (BuildFeatureConstants.CCACHEEXECUTABLE.name, "ccache"),
        (BuildFeatureConstants.SCCACHEEXECUTABLE.name, "sccache"),
        (BuildFeatureConstants.BUILDCACHEEXECUTABLE.name, "buildcache"),
    ],
)
# pylint: disable=too-many-arguments, too-many-positional-arguments  # noqa: E501
def test_conan_autotoolsbuildhelper_make(
    reply_queue_fixture: typing.Callable[
        [], typing.Tuple[queue.Queue[Message], typing.List[Message], threading.Thread]
    ],
    conan_autotoolsbuildenvironment_make_recipe: pathlib.Path,
    conan_local_cache: typing.Dict[str, str],
    _configure_script: pathlib.Path,
    _makefile: pathlib.Path,
    custom_make_command: pathlib.Path,
    env_key: typing.Optional[str],
    env_value: typing.Optional[str],
    monkeypatch: pytest.MonkeyPatch,
    conanised_os: str,
) -> None:
    """
    Test: running the AutoToolsBuildEnvironment helper make method.

    conan install is a required prerequisite.
    """
    pytest.mark.skipif(conanised_os == "win", "Not configured for autotools on Windows")
    if CONAN_MAJOR_VERSION == 1:
        worker = workers_api.install.invoke
        params = CommandParameters("install", worker)
        params.added_environment = conan_local_cache
        params.recipe_path = conan_autotoolsbuildenvironment_make_recipe
        params.cwd = conan_autotoolsbuildenvironment_make_recipe.parent
        params.profile = "default"
        reply_queue, replies, watcher_thread = reply_queue_fixture()
        # abusing the type system, as the API used for queue.Queue is the same
        # as for multiprocessing.Queue
        worker(reply_queue, params)  # type: ignore[arg-type]
        watcher_thread.join(timeout=5.0)
        if watcher_thread.is_alive():
            raise texceptions.WatcherThreadTimeoutError()

    if env_key and env_value:
        monkeypatch.setenv(env_key, env_value)

    worker = workers_api.build.invoke
    params = CommandParameters("build", worker)
    params.added_environment = conan_local_cache
    params.added_environment["CONAN_MAKE_PROGRAM"] = os.fspath(custom_make_command)
    params.recipe_path = conan_autotoolsbuildenvironment_make_recipe
    params.cwd = conan_autotoolsbuildenvironment_make_recipe.parent
    reply_queue, replies, watcher_thread = reply_queue_fixture()
    # abusing the type system, as the API used for queue.Queue is the same
    # as for multiprocessing.Queue
    worker(reply_queue, params)  # type: ignore[arg-type]
    watcher_thread.join(timeout=5.0)
    if watcher_thread.is_alive():
        raise texceptions.WatcherThreadTimeoutError()

    assert replies
    assert isinstance(replies[0], Success)
