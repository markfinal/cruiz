"""
Test the conan create functionality, in a single process.

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

# pylint: disable=import-error
import testexceptions


LOGGER = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "arg,value",
    [
        (None, None),
        ("version", "conan_recipe_version"),
        ("options", {"shared": "True"}),
        (("user", "channel"), ("user1", "channel1")),
        # (conan2) conan create <path> works but conan create --update <path>
        # defaults to the current directory - there is documentation saying this
        # happens, but not for adding --update
        pytest.param(
            "arguments",
            ["--update"],
            marks=pytest.mark.xfail(
                CONAN_VERSION_COMPONENTS > (2, 0, 14),
                reason="Unexpected Conan 2 create behaviour with --update",
            ),
        ),
    ],
)
# pylint: disable=too-many-arguments, too-many-positional-arguments, too-many-branches, too-many-locals  # noqa: E501
def test_conan_create(
    reply_queue_fixture: typing.Callable[
        [], typing.Tuple[queue.Queue[Message], typing.List[Message], threading.Thread]
    ],
    conan_recipe: pathlib.Path,
    conan_local_cache: typing.Dict[str, str],
    arg: typing.Optional[str],
    value: typing.Optional[str],
    request: pytest.FixtureRequest,
    conan_recipe_name: str,
) -> None:
    """Test: running conan create."""
    worker = workers_api.create.invoke
    params = CommandParameters("create", worker)
    params.added_environment = conan_local_cache
    params.recipe_path = conan_recipe
    params.profile = "default"
    # params.cwd = conan_recipe.parent
    if arg and value:
        if isinstance(value, dict):
            if arg == "options":
                for key, val in value.items():
                    params.add_option(conan_recipe_name, key, val)
        elif isinstance(arg, tuple):
            for key, value_for_key in zip(arg, value):
                setattr(params, key, value_for_key)
        elif isinstance(value, list):
            if arg == "arguments":
                params.arguments.extend(value)
        else:
            try:
                true_value = request.getfixturevalue(value)
            except pytest.FixtureLookupError:
                true_value = value
            setattr(params, arg, true_value)
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
        raise testexceptions.WatcherThreadTimeoutError()

    assert replies
    assert isinstance(replies[0], Success)
    if CONAN_MAJOR_VERSION == 1:
        assert isinstance(replies[0].payload, dict)
        assert "error" in replies[0].payload and not replies[0].payload["error"]
        assert "installed" in replies[0].payload
    else:
        assert replies[0].payload is None
