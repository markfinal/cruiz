"""
Test the conan test functionality, in a single process.

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

# pylint: disable=wrong-import-order
import pytest

if typing.TYPE_CHECKING:
    from ttypes import MultiprocessReplyQueueFixture, RunWorkerFixture


LOGGER = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "arg,value",
    [
        (None, None),
        ("options", {"shared": "True"}),
        ("test_build_folder", "testme"),
    ],
)
# pylint: disable=too-many-arguments, too-many-positional-arguments, too-many-locals  # noqa: E501
def test_conan_test(
    multiprocess_reply_queue_fixture: MultiprocessReplyQueueFixture,
    run_worker: RunWorkerFixture,
    conan_recipe: pathlib.Path,
    conan_testpackage_recipe: pathlib.Path,
    conan_recipe_name: str,
    conan_recipe_version: str,
    conan_local_cache: typing.Dict[str, str],
    arg: typing.Optional[str],
    value: typing.Union[typing.Optional[str], typing.List[str], typing.Dict[str, str]],
    tmp_path: pathlib.Path,
) -> None:
    """
    Test: running conan test.

    conan create is a required prerequisite, to test the exported package.
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
    reply_queue, replies, watcher_thread, context = multiprocess_reply_queue_fixture()
    run_worker(worker, reply_queue, params, watcher_thread, context)

    worker = workers_api.testpackage.invoke
    params = CommandParameters("test", worker)
    params.added_environment = conan_local_cache
    params.recipe_path = conan_testpackage_recipe
    params.cwd = conan_testpackage_recipe.parent
    params.profile = "default"
    params.name = conan_recipe_name
    params.version = conan_recipe_version
    if CONAN_VERSION_COMPONENTS == (1, 17, 1):
        params.user = "user1"
        params.channel = "channel1"
    params.make_package_reference()
    params.v2_need_reference = True
    if arg and value:
        if arg == "options":
            assert isinstance(value, dict)
            for key, val in value.items():
                params.add_option(conan_recipe_name, key, val)
        elif arg == "test_build_folder":
            assert isinstance(value, str)
            params.test_build_folder = tmp_path / value
    reply_queue, replies, watcher_thread, context = multiprocess_reply_queue_fixture()
    run_worker(worker, reply_queue, params, watcher_thread, context)

    assert replies
    assert isinstance(replies[0], Success)
