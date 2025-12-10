"""
Test the conan build functionality, in a single process.

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
            "build_folder",
            "build",
            marks=pytest.mark.skipif(
                CONAN_MAJOR_VERSION == 2,
                reason="Build folder not supported in Conan 2",
            ),
        ),
        pytest.param(
            "package_folder",
            "package",
            marks=pytest.mark.skipif(
                CONAN_MAJOR_VERSION == 2,
                reason="Package folder not supported in Conan 2",
            ),
        ),
    ],
)
# pylint: disable=too-many-arguments, too-many-positional-arguments  # noqa: E501
def test_conan_build(
    reply_queue_fixture: SingleprocessReplyQueueFixture,
    run_worker: RunWorkerFixture,
    conan_recipe: pathlib.Path,
    conan_local_cache: typing.Dict[str, str],
    tmp_path: pathlib.Path,
    arg: typing.Optional[str],
    value: typing.Union[typing.Optional[str], typing.List[str], typing.Dict[str, str]],
) -> None:
    """
    Test: running conan build.

    conan install is a required prerequisite.
    """
    if CONAN_MAJOR_VERSION == 1:
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
        reply_queue, replies, watcher_thread, context = reply_queue_fixture()
        run_worker(worker, reply_queue, params, watcher_thread, context)

    worker = workers_api.build.invoke
    params = CommandParameters("build", worker)
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
    reply_queue, replies, watcher_thread, context = reply_queue_fixture()
    run_worker(worker, reply_queue, params, watcher_thread, context)

    assert replies
    assert isinstance(replies[0], Success)
