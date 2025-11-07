"""Common fixtures for workers."""

from __future__ import annotations

import logging
import multiprocessing
import os
import pathlib
import platform
import queue
import threading
import typing

import cruizlib.workers.api as workers_api
from cruizlib.globals import CONAN_MAJOR_VERSION
from cruizlib.interop.commandparameters import CommandParameters
from cruizlib.interop.message import (
    ConanLogMessage,
    End,
    Failure,
    Message,
    Stderr,
    Stdout,
    Success,
)

# pylint: disable=import-error,wrong-import-order
import testexceptions

if typing.TYPE_CHECKING:
    from cruizlib.multiprocessingmessagequeuetype import (
        MultiProcessingMessageQueueType,
    )

# pylint: disable=wrong-import-order, wrong-import-position
import pytest

LOGGER = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def _do_not_run_tests_with_default_conan_local_caches() -> typing.Generator[None]:
    """
    Fixture to ensure the default local cache directory is not present.

    If it is present, it can indicate a test not being set up correctly.
    """

    def _check_default_conan_cache_does_not_exist() -> None:
        if CONAN_MAJOR_VERSION == 1:
            assert not (
                pathlib.Path.home() / ".conan"
            ).exists(), "Do not run tests in the presense of a default local cache"
        else:
            assert not (pathlib.Path.home() / ".conan2").exists(), (
                "Default local cache exists after tests complete;"
                "are tests incorrectly configured?"
            )

    _check_default_conan_cache_does_not_exist()
    yield
    _check_default_conan_cache_does_not_exist()


@pytest.fixture(name="conanised_os")
def fixture_connanised_os() -> str:
    """Return the Conan terminology for the current OS."""
    plat = platform.system()
    if plat == "Darwin":
        return "Macos"
    return plat


@pytest.fixture(name="conan_local_cache")
def fixture_conan_local_cache(
    tmp_path: pathlib.Path, conanised_os: str
) -> typing.Dict[str, str]:
    """Refer to a temporary Conan local cache."""
    if CONAN_MAJOR_VERSION == 1:
        env = {"CONAN_USER_HOME": os.fspath(tmp_path)}
        profile_dir = tmp_path / ".conan" / "profiles"
    else:
        env = {"CONAN_HOME": os.fspath(tmp_path / ".conan2")}
        profile_dir = tmp_path / ".conan2" / "profiles"

    # create a dummy default profile
    profile_dir.mkdir(parents=True)
    with (profile_dir / "default").open("wt", encoding="utf-8") as profile:
        profile.write("[settings]\n")
        profile.write(f"os={conanised_os}\n")
        profile.write("[options]\n")

    return env


# TODO: unable to write the return type I'm interested in, as Python keeps erroring
# see where this fixture is used for the type intented
@pytest.fixture()
def meta(
    conan_local_cache: typing.Dict[str, str],
) -> typing.Generator[typing.Tuple[typing.Any, typing.Any], None, None]:
    """
    Fixture for setup and teardown of meta processes and queues.

    On the test process, a request and reply queue are created.
    And then a subprocess running the worker is started.

    On teardown, the request queue is finished, and joined.
    Then the responses are joined.

    Finally the subprocess is joined.
    """
    params = CommandParameters("meta", workers_api.meta.invoke)
    params.added_environment = conan_local_cache
    context = multiprocessing.get_context("spawn")
    request_queue = context.JoinableQueue()
    reply_queue = context.Queue()
    process = context.Process(
        target=params.worker,
        args=(request_queue, reply_queue, params),
        daemon=False,
    )
    process.start()

    yield request_queue, reply_queue

    # close down request
    request_queue.put(End())
    request_queue.join()

    # wait for the requests to finish
    request_queue.close()
    request_queue.join_thread()

    # wait for the responses to finish
    reply_queue.close()
    reply_queue.join_thread()

    # wait for the child process to finish
    process.join()
    process.close()


class TestableThread(threading.Thread):
    """
    Wrapper around `threading.Thread` that propagates exceptions.

    REF: https://gist.github.com/sbrugman/59b3535ebcd5aa0e2598293cfa58b6ab
    """

    def __init__(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        """Subclassed from threading.Thread."""
        super().__init__(*args, **kwargs)
        self.exc: typing.Optional[BaseException] = None

    def run(self) -> None:
        """Subclassed from threading.Thread."""
        try:
            super().run()
        # pylint: disable=broad-exception-caught
        except BaseException as e:  # noqa: B036
            self.exc = e

    def join(self, timeout: typing.Optional[float] = None) -> None:
        """Subclassed from threading.Thread."""
        super().join(timeout)
        if self.exc:
            raise self.exc


@pytest.fixture()
def reply_queue_fixture() -> (
    typing.Tuple[queue.Queue[Message], typing.List[Message], TestableThread]
):
    """
    Fixture to create a reply queue for a worker invocation on the same process.

    Uses a thread for message processing.
    The calling test must join the thread, before making any assertions on the
    responses.
    """

    def _reply_watcher(
        reply_queue: queue.Queue[Message], replies: typing.List[Message]
    ) -> None:
        while True:
            reply = reply_queue.get()
            if isinstance(reply, Success):
                replies.append(reply)
                break
            if isinstance(reply, Failure):
                raise testexceptions.FailedMessageTestError() from reply.exception
            if isinstance(reply, (ConanLogMessage, Stdout, Stderr)):
                LOGGER.info("Message: '%s'", reply.message)
                continue
            raise ValueError(f"Unknown reply of type '{type(reply)}'")

    reply_queue = queue.Queue[Message]()
    replies: typing.List[Message] = []
    watcher_thread = TestableThread(target=_reply_watcher, args=(reply_queue, replies))
    watcher_thread.start()
    return reply_queue, replies, watcher_thread


@pytest.fixture()
def multiprocess_reply_queue_fixture() -> typing.Tuple[
    MultiProcessingMessageQueueType,
    typing.List[Message],
    TestableThread,
    typing.Any,
]:
    """
    Fixture to create a reply queue for a worker invocation on a child process.

    Uses a thread for message processing.
    The calling test must join the thread, before making any assertions on the
    responses.
    """

    def _reply_watcher(
        reply_queue: MultiProcessingMessageQueueType, replies: typing.List[Message]
    ) -> None:
        try:
            while True:
                reply = reply_queue.get()
                if isinstance(reply, Success):
                    replies.append(reply)
                    break
                if isinstance(reply, Failure):
                    raise testexceptions.FailedMessageTestError() from reply.exception
                if isinstance(reply, (ConanLogMessage, Stdout, Stderr)):
                    LOGGER.info("Message: '%s'", reply.message)
                    continue
                raise ValueError(f"Unknown reply of type '{type(reply)}'")
        finally:
            reply_queue.close()
            reply_queue.join_thread()

    context = multiprocessing.get_context("spawn")
    reply_queue = context.Queue()
    replies: typing.List[Message] = []
    watcher_thread = TestableThread(target=_reply_watcher, args=(reply_queue, replies))
    watcher_thread.start()
    return reply_queue, replies, watcher_thread, context


@pytest.fixture(name="conan_recipe_name_invalid")
def fixture_conan_recipe_name_invalid() -> str:
    """Return an invalid recipe name."""
    return "pkg_does_not_exist"


@pytest.fixture(name="conan_recipe_name")
def fixture_conan_recipe_name() -> str:
    """Return the name of the conan recipe to use."""
    return "test"


@pytest.fixture(name="conan_recipe_version")
def fixture_conan_recipe_version() -> str:
    """Return the version of the conan recipe to use."""
    return "3.4.5"


@pytest.fixture(name="conan_recipe_pkgref")
def fixture_conan_recipe_pkgref(
    conan_recipe_name: str, conan_recipe_version: str
) -> str:
    """Return the package reference generated from the recipe."""
    return f"{conan_recipe_name}/{conan_recipe_version}"


@pytest.fixture(name="conan_recipe_pkgref_namespaced")
def fixture_conan_recipe_pkgref_namespaced(
    conan_recipe_name: str, conan_recipe_version: str
) -> str:
    """Return the package reference generated from the recipe with a user/channel."""
    return f"{conan_recipe_name}/{conan_recipe_version}@cruiz/stable"


@pytest.fixture()
def conan_recipe(
    tmp_path: pathlib.Path, conan_recipe_name: str, conan_recipe_version: str
) -> pathlib.Path:
    """Create and return path to a Conan recipe."""
    recipe_path = tmp_path / "conanfile.py"
    with recipe_path.open("wt", encoding="utf-8") as conanfile:
        if CONAN_MAJOR_VERSION == 1:
            conanfile.write("from conans import ConanFile\n")
            conanfile.write("class TestConanFile(ConanFile):\n")
        else:
            conanfile.write("from conan import ConanFile\n")
            conanfile.write("class TestConanFile(ConanFile):\n")
        conanfile.write(f"  name = '{conan_recipe_name}'\n")
        conanfile.write(f"  version = '{conan_recipe_version}'\n")
        conanfile.write("  options = {'shared': [True, False]}\n")
        conanfile.write("  default_options = {'shared': True}\n")
    return recipe_path


@pytest.fixture()
def conan_recipe_invalid(tmp_path: pathlib.Path) -> pathlib.Path:
    """Return an invalid path to a recipe."""
    return tmp_path / "does_not_exist.py"


@pytest.fixture(name="_installed_hook")
def fixture_installed_hook(conan_local_cache: typing.Dict[str, str]) -> pathlib.Path:
    """Fixture that installs a hook into the local cache."""
    if CONAN_MAJOR_VERSION == 1:
        conan_local_cache_dir = pathlib.Path(conan_local_cache["CONAN_USER_HOME"])
    else:
        conan_local_cache_dir = pathlib.Path(conan_local_cache["CONAN_HOME"])

    hook_path = conan_local_cache_dir / "hooks" / "my_hook.py"
    hook_path.parent.mkdir(parents=True)
    with hook_path.open("wt", encoding="utf-8") as hook_file:
        hook_file.write("# a hook\n")
    return hook_path
