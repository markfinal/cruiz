"""
Test the conan lock create functionality, in a single process.

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
from cruizlib.globals import CONAN_VERSION_COMPONENTS
from cruizlib.interop.commandparameters import CommandParameters
from cruizlib.interop.dependencygraph import DependencyGraph
from cruizlib.interop.message import (
    Message,
    Success,
)

# pylint: disable=wrong-import-order
import pytest

import testexceptions


LOGGER = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "arg,value",
    [
        (None, None),
        ("options", {"shared": "True"}),
    ],
)
# "'DepsGraph' object has no attribute 'build_time_nodes'" from v2.0.15
@pytest.mark.xfail(
    CONAN_VERSION_COMPONENTS >= (2, 0, 15),
    reason="build_time_nodes removed in Conan 2.0.15",
    raises=testexceptions.FailedMessageTestError,
    strict=True,
)
# pylint: disable=too-many-arguments, too-many-positional-arguments
def test_conan_lock_create(
    reply_queue_fixture: typing.Callable[
        [], typing.Tuple[queue.Queue[Message], typing.List[Message], threading.Thread]
    ],
    conan_recipe_name: str,
    conan_recipe: pathlib.Path,
    conan_local_cache: typing.Dict[str, str],
    arg: typing.Optional[str],
    value: typing.Union[typing.Optional[str], typing.List[str], typing.Dict[str, str]],
) -> None:
    """Test: running conan lock create."""
    worker = workers_api.lockcreate.invoke
    params = CommandParameters("lock create", worker)
    params.added_environment = conan_local_cache
    params.recipe_path = conan_recipe
    params.cwd = conan_recipe.parent
    params.profile = "default"
    if arg == "options":
        assert isinstance(value, dict)
        for key, val in value.items():
            params.add_option("test", key, val)

    reply_queue, replies, watcher_thread = reply_queue_fixture()
    # abusing the type system, as the API used for queue.Queue is the same
    # as for multiprocessing.Queue
    worker(reply_queue, params)  # type: ignore[arg-type]
    watcher_thread.join(timeout=5.0)
    if watcher_thread.is_alive():
        raise testexceptions.WatcherThreadTimeoutError()

    assert replies
    assert isinstance(replies[0], Success)
    assert isinstance(replies[0].payload, DependencyGraph)
    assert len(replies[0].payload.nodes) == 1
    assert replies[0].payload.root.name == conan_recipe_name


# "'DepsGraph' object has no attribute 'build_time_nodes'" from v2.0.15
@pytest.mark.xfail(
    CONAN_VERSION_COMPONENTS >= (2, 0, 15),
    reason="build_time_nodes removed in Conan 2.0.15",
    raises=testexceptions.FailedMessageTestError,
    strict=True,
)
def test_conan_lock_create_dependent_recipes(
    reply_queue_fixture: typing.Callable[
        [], typing.Tuple[queue.Queue[Message], typing.List[Message], threading.Thread]
    ],
    conan_dependent_recipes: typing.Tuple[
        pathlib.Path, str, str, pathlib.Path, str, str
    ],
    conan_local_cache: typing.Dict[str, str],
) -> None:
    """Test: running conan lock create, with two dependent recipes."""
    worker = workers_api.exportpackage.invoke
    params = CommandParameters("exportpkg", worker)
    params.added_environment = conan_local_cache
    params.recipe_path = conan_dependent_recipes[0]
    params.cwd = conan_dependent_recipes[0].parent
    params.profile = "default"
    params.name = conan_dependent_recipes[1]
    if CONAN_VERSION_COMPONENTS == (1, 17, 1):
        # since this early Conan version requires a user and channel on pkgrefs
        # if the test overrides params.user or params.channel, this will go wrong
        # in Conan 1.17.1
        params.user = params.user or "test_user"
        params.channel = params.channel or "test_channel"

    reply_queue, replies, watcher_thread = reply_queue_fixture()
    # abusing the type system, as the API used for queue.Queue is the same
    # as for multiprocessing.Queue
    worker(reply_queue, params)  # type: ignore[arg-type]
    watcher_thread.join(timeout=5.0)
    if watcher_thread.is_alive():
        raise testexceptions.WatcherThreadTimeoutError()

    assert replies
    assert isinstance(replies[0], Success)

    worker = workers_api.lockcreate.invoke
    params = CommandParameters("lock create", worker)
    params.added_environment = conan_local_cache
    params.recipe_path = conan_dependent_recipes[3]
    params.cwd = conan_dependent_recipes[3].parent
    params.profile = "default"

    reply_queue, replies, watcher_thread = reply_queue_fixture()
    # abusing the type system, as the API used for queue.Queue is the same
    # as for multiprocessing.Queue
    worker(reply_queue, params)  # type: ignore[arg-type]
    watcher_thread.join(timeout=5.0)
    if watcher_thread.is_alive():
        raise testexceptions.WatcherThreadTimeoutError()

    assert replies
    assert isinstance(replies[0], Success)
    assert isinstance(replies[0].payload, DependencyGraph)
    assert len(replies[0].payload.nodes) == 2
    assert replies[0].payload.root == replies[0].payload.nodes[1]
    assert replies[0].payload.nodes[1].name == conan_dependent_recipes[4]
    assert replies[0].payload.nodes[0].name == conan_dependent_recipes[1]
    assert len(replies[0].payload.root.children) == 1
    assert len(replies[0].payload.root.children[0].parents) == 1
