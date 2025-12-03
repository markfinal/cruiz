"""
Test the conan CMake 1 helper functionality, in a single process.

Note that this is not how cruiz tends to work, and should be using multiple processes
to isolate the Conan commands, but this test shows it still works without that
added complexity.
"""

from __future__ import annotations

import logging
import pathlib
import typing

import cruizlib.workers.api as workers_api
from cruizlib.constants import BuildFeatureConstants
from cruizlib.globals import CONAN_MAJOR_VERSION
from cruizlib.interop.commandparameters import CommandParameters
from cruizlib.interop.message import Success

# pylint: disable=wrong-import-order
import pytest

if typing.TYPE_CHECKING:
    from ttypes import MultiprocessReplyQueueFixture, RunWorkerFixture


LOGGER = logging.getLogger(__name__)


@pytest.mark.skipif(
    CONAN_MAJOR_VERSION == 2, reason="Conan 2 does not support this CMake helper."
)
@pytest.mark.parametrize(
    "env_key,env_value",
    [
        (None, None),
        (BuildFeatureConstants.CMAKEFINDDEBUGMODE.name, "TRUE"),
        (BuildFeatureConstants.CMAKEVERBOSEMODE.name, "TRUE"),
        (BuildFeatureConstants.CCACHEEXECUTABLE.name, "ccache"),
        (BuildFeatureConstants.SCCACHEEXECUTABLE.name, "sccache"),
        (BuildFeatureConstants.BUILDCACHEEXECUTABLE.name, "buildccache"),
    ],
)
# pylint: disable=too-many-arguments, too-many-positional-arguments  # noqa: E501
def test_conan_cmake_helper(
    multiprocess_reply_queue_fixture: MultiprocessReplyQueueFixture,
    run_worker: RunWorkerFixture,
    conan_cmake_helper_recipe: pathlib.Path,
    conan_local_cache: typing.Dict[str, str],
    _cmake_script: pathlib.Path,
    env_key: typing.Optional[str],
    env_value: typing.Optional[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Test: running the CMake helper configure method.

    conan install is a required prerequisite.
    """
    if CONAN_MAJOR_VERSION == 1:
        worker = workers_api.install.invoke
        params = CommandParameters("install", worker)
        params.added_environment = conan_local_cache
        params.recipe_path = conan_cmake_helper_recipe
        params.cwd = conan_cmake_helper_recipe.parent
        params.profile = "default"
        reply_queue, replies, watcher_thread, context = (
            multiprocess_reply_queue_fixture()
        )
        run_worker(worker, reply_queue, params, watcher_thread, context)

    if env_key and env_value:
        monkeypatch.setenv(env_key, env_value)

    worker = workers_api.build.invoke
    params = CommandParameters("build", worker)
    params.added_environment = conan_local_cache
    params.recipe_path = conan_cmake_helper_recipe
    params.cwd = conan_cmake_helper_recipe.parent
    reply_queue, replies, watcher_thread, context = multiprocess_reply_queue_fixture()
    run_worker(worker, reply_queue, params, watcher_thread, context)

    assert replies
    assert isinstance(replies[0], Success)
