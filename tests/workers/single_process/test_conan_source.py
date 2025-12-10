"""
Test the conan source functionality, in a single process.

Note that this is not how cruiz tends to work, and should be using multiple processes
to isolate the Conan commands, but this test shows it still works without that
added complexity.
"""

from __future__ import annotations

import logging
import pathlib
import typing

import cruizlib.workers.api as workers_api
from cruizlib.globals import CONAN_MAJOR_VERSION
from cruizlib.interop.commandparameters import CommandParameters
from cruizlib.interop.message import Success

# pylint: disable=wrong-import-order
import pytest

if typing.TYPE_CHECKING:
    from ttypes import RunWorkerFixture, SingleprocessReplyQueueFixture


LOGGER = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "arg,value",
    [
        (None, None),
        pytest.param(
            "install_folder",
            "install",
            marks=pytest.mark.skipif(
                CONAN_MAJOR_VERSION == 2,
                reason="Install folder not supported in Conan 2",
            ),
        ),
        pytest.param(
            "source_folder",
            "src",
            marks=pytest.mark.skipif(
                CONAN_MAJOR_VERSION == 2,
                reason="Source folder not supported in Conan 2",
            ),
        ),
        pytest.param(
            "name",
            "conan_recipe_name",
            marks=pytest.mark.skipif(
                CONAN_MAJOR_VERSION == 1,
                reason="name not supported in Conan 1",
            ),
        ),
        pytest.param(
            "version",
            "conan_recipe_version",
            marks=pytest.mark.skipif(
                CONAN_MAJOR_VERSION == 1,
                reason="version not supported in Conan 1",
            ),
        ),
        pytest.param(
            "user",
            "my_user",
            marks=pytest.mark.skipif(
                CONAN_MAJOR_VERSION == 1,
                reason="user not supported in Conan 1",
            ),
        ),
        pytest.param(
            ("user", "channel"),
            ("my_user", "my_channel"),
            marks=pytest.mark.skipif(
                CONAN_MAJOR_VERSION == 1,
                reason="channel not supported in Conan 1",
            ),
        ),
    ],
)
# pylint: disable=too-many-arguments, too-many-positional-arguments
def test_conan_source(
    reply_queue_fixture: SingleprocessReplyQueueFixture,
    run_worker: RunWorkerFixture,
    conan_recipe: pathlib.Path,
    conan_local_cache: typing.Dict[str, str],
    tmp_path: pathlib.Path,
    arg: typing.Optional[str],
    value: typing.Union[typing.Optional[str], typing.List[str], typing.Dict[str, str]],
    request: pytest.FixtureRequest,
) -> None:
    """
    Test: running conan source.

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
        reply_queue, replies, watcher_thread, context = reply_queue_fixture()
        run_worker(worker, reply_queue, params, watcher_thread, context)

    worker = workers_api.source.invoke
    params = CommandParameters("source", worker)
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
        elif arg == "name":
            assert isinstance(value, str)
            params.name = request.getfixturevalue(value)
        elif arg == "version":
            assert isinstance(value, str)
            params.version = request.getfixturevalue(value)
        elif arg == "user":
            assert isinstance(value, str)
            params.user = value
        elif arg == "channel":
            assert isinstance(value, str)
            params.channel = value
        elif isinstance(arg, tuple) and arg == ("user", "channel"):
            assert isinstance(value, tuple)
            params.user = value[0]
            params.channel = value[1]
    reply_queue, replies, watcher_thread, context = reply_queue_fixture()
    run_worker(worker, reply_queue, params, watcher_thread, context)

    assert replies
    assert isinstance(replies[0], Success)
