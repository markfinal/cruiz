"""Common fixtures for workers."""

from __future__ import annotations

import json
import logging
import multiprocessing
import os
import pathlib
import platform
import queue
import stat
import threading
import typing

import cruizlib.workers.api as workers_api
from cruizlib.globals import CONAN_MAJOR_VERSION, CONAN_VERSION_COMPONENTS
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

# pylint: disable=wrong-import-order
import texceptions

if typing.TYPE_CHECKING:
    from cruizlib.multiprocessingmessagequeuetype import (
        MultiProcessingMessageQueueType,
    )

# pylint: disable=wrong-import-order, wrong-import-position
import pytest

import yaml

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
    """
    Refer to a temporary Conan local cache.

    Environment variables are set for Conan to pick up.
    As these differ between Conan 1 and Conan 2, an additional test specific environemnt
    variable is set with the _true_ local cache directory for tests to use,
    _REAL_CONAN_LOCAL_CACHE_DIR.
    """
    if CONAN_MAJOR_VERSION == 1:
        local_cache_dir = tmp_path / ".conan"
        env = {
            "CONAN_USER_HOME": os.fspath(tmp_path),
            "_REAL_CONAN_LOCAL_CACHE_DIR": os.fspath(local_cache_dir),
        }
    else:
        local_cache_dir = tmp_path / ".conan2"
        env = {
            "CONAN_HOME": os.fspath(local_cache_dir),
            "_REAL_CONAN_LOCAL_CACHE_DIR": os.fspath(local_cache_dir),
        }

    # create a dummy default profile
    profile_dir = local_cache_dir / "profiles"
    profile_dir.mkdir(parents=True)
    with (profile_dir / "default").open("wt", encoding="utf-8") as profile:
        profile.write("[settings]\n")
        profile.write(f"os={conanised_os}\n")
        profile.write("[options]\n")

    # create default remote
    remotes_file = local_cache_dir / "remotes.json"
    with remotes_file.open("wt", encoding="utf-8") as remotes:
        remotes_data = {
            "remotes": [
                {
                    "name": "conancenter",
                    "url": "https://center.conan.io",
                    "verify_ssl": True,
                }
            ]
        }
        json.dump(remotes_data, remotes)

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
def reply_queue_fixture() -> typing.Callable[
    [],
    typing.Tuple[queue.Queue[Message], typing.List[Message], TestableThread],
]:
    """
    Fixture factory to create a reply queue for a worker invocation on the same process.

    It is a factory because the fixture may need to be invoked several times during
    a test to generate new queues.

    Uses a thread for message processing.
    The calling test must join the thread, before making any assertions on the
    responses.
    """

    def _the_fixture() -> (
        typing.Tuple[queue.Queue[Message], typing.List[Message], TestableThread]
    ):
        def _reply_watcher(
            reply_queue: queue.Queue[Message], replies: typing.List[Message]
        ) -> None:
            while True:
                reply = reply_queue.get(timeout=10)
                if isinstance(reply, Success):
                    assert not replies
                    replies.append(reply)
                elif isinstance(reply, Failure):
                    raise texceptions.FailedMessageTestError(
                        reply.message or "<Empty message from upstream>",
                        reply.exception_type_name,
                        reply.exception_traceback,
                    )
                elif isinstance(reply, (ConanLogMessage, Stdout, Stderr)):
                    LOGGER.info(reply.message)
                else:
                    raise ValueError(f"Unknown reply of type '{type(reply)}'")
                if reply_queue.empty() and replies:
                    break

        reply_queue = queue.Queue[Message]()
        replies: typing.List[Message] = []
        watcher_thread = TestableThread(
            target=_reply_watcher, args=(reply_queue, replies)
        )
        watcher_thread.start()
        return reply_queue, replies, watcher_thread

    return _the_fixture


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
                reply = reply_queue.get(timeout=10)
                if isinstance(reply, Success):
                    assert not replies
                    replies.append(reply)
                elif isinstance(reply, Failure):
                    raise texceptions.FailedMessageTestError(
                        reply.message or "<Empty message from upstream>",
                        reply.exception_type_name,
                        reply.exception_traceback,
                    )
                elif isinstance(reply, End):
                    LOGGER.info("EndOfLine")
                    assert not replies
                    replies.append(Success(None))
                elif isinstance(reply, (ConanLogMessage, Stdout, Stderr)):
                    LOGGER.info(reply.message)
                    continue
                else:
                    raise ValueError(f"Unknown reply of type '{type(reply)}'")
                if reply_queue.empty() and replies:
                    break
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
def conan_cmake_helper_recipe(
    tmp_path: pathlib.Path, conan_recipe_name: str, conan_recipe_version: str
) -> pathlib.Path:
    """Create and return path to a Conan recipe using the CMake helper in Conan 1."""
    recipe_path = tmp_path / "conanfile.py"
    with recipe_path.open("wt", encoding="utf-8") as conanfile:
        if CONAN_MAJOR_VERSION == 1:
            conanfile.write("from conans import ConanFile, CMake\n")
            conanfile.write("class TestConanFile(ConanFile):\n")
        else:
            conanfile.write("from conan import ConanFile\n")
            conanfile.write("class TestConanFile(ConanFile):\n")
        conanfile.write(f"  name = '{conan_recipe_name}'\n")
        conanfile.write(f"  version = '{conan_recipe_version}'\n")
        conanfile.write("  options = {'shared': [True, False]}\n")
        conanfile.write("  default_options = {'shared': True}\n")
        if CONAN_MAJOR_VERSION == 1:
            conanfile.write("  def build(self):\n")
            conanfile.write("    cmake = CMake(self)\n")
            conanfile.write("    cmake.configure()\n")
    return recipe_path


@pytest.fixture(name="_cmake_script")
def fixture_cmake_script(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create and return path to a CMakeLists.txt."""
    cmake_script_path = tmp_path / "CMakeLists.txt"
    with cmake_script_path.open("wt", encoding="utf-8") as cmake_script_file:
        cmake_script_file.write("cmake_minimum_required(VERSION 3.31 FATAL_ERROR)")
    return cmake_script_path


@pytest.fixture()
def conan_autotoolsbuildenvironment_configure_recipe(
    tmp_path: pathlib.Path, conan_recipe_name: str, conan_recipe_version: str
) -> pathlib.Path:
    """
    Create and return path to a Conan recipe using the AutoToolsBuildEnvironment.

    This helper is only in Conan 1.

    This recipe only calls the configure method.
    """
    recipe_path = tmp_path / "conanfile.py"
    with recipe_path.open("wt", encoding="utf-8") as conanfile:
        if CONAN_MAJOR_VERSION == 1:
            conanfile.write(
                "from conans import ConanFile, AutoToolsBuildEnvironment, tools\n"
            )
            conanfile.write("class TestConanFile(ConanFile):\n")
        else:
            conanfile.write("from conan import ConanFile\n")
            conanfile.write("class TestConanFile(ConanFile):\n")
        conanfile.write(f"  name = '{conan_recipe_name}'\n")
        conanfile.write(f"  version = '{conan_recipe_version}'\n")
        conanfile.write("  settings = 'os'\n")
        conanfile.write("  options = {'shared': [True, False]}\n")
        conanfile.write("  default_options = {'shared': True}\n")
        if CONAN_MAJOR_VERSION == 1:
            conanfile.write("  def build(self):\n")
            conanfile.write(
                "    at = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)\n"  # pylint: disable=line-too-long  # noqa: E501
            )
            conanfile.write("    at.configure()\n")
    return recipe_path


@pytest.fixture()
def conan_autotoolsbuildenvironment_make_recipe(
    tmp_path: pathlib.Path, conan_recipe_name: str, conan_recipe_version: str
) -> pathlib.Path:
    """
    Create and return path to a Conan recipe using the AutoToolsBuildEnvironment.

    This helper is only in Conan 1.

    This recipe calls the configure and make methods.
    """
    recipe_path = tmp_path / "conanfile.py"
    with recipe_path.open("wt", encoding="utf-8") as conanfile:
        if CONAN_MAJOR_VERSION == 1:
            conanfile.write(
                "from conans import ConanFile, AutoToolsBuildEnvironment, tools\n"
            )
            conanfile.write("class TestConanFile(ConanFile):\n")
        else:
            conanfile.write("from conan import ConanFile\n")
            conanfile.write("class TestConanFile(ConanFile):\n")
        conanfile.write(f"  name = '{conan_recipe_name}'\n")
        conanfile.write(f"  version = '{conan_recipe_version}'\n")
        conanfile.write("  options = {'shared': [True, False]}\n")
        conanfile.write("  default_options = {'shared': True}\n")
        if CONAN_MAJOR_VERSION == 1:
            conanfile.write("  def build(self):\n")
            conanfile.write(
                "    at = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)\n"  # pylint: disable=line-too-long  # noqa: E501
            )
            conanfile.write("    at.configure()\n")
            conanfile.write("    at.make()\n")
    return recipe_path


@pytest.fixture(name="_configure_script")
def fixture_configure_script(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create and return path to a configure script."""
    configure_script_path = tmp_path / "configure"
    with configure_script_path.open("wt", encoding="utf-8") as configure_script_file:
        configure_script_file.write("#!/usr/bin/env sh")
    configure_script_path.chmod(configure_script_path.stat().st_mode | stat.S_IEXEC)
    return configure_script_path


@pytest.fixture(name="_makefile")
def fixture_makefile(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create and return path to a Makefile."""
    makefile_path = tmp_path / "Makefile"
    with makefile_path.open("wt", encoding="utf-8") as makefile_file:
        makefile_file.write("# empty")
    return makefile_path


@pytest.fixture(name="custom_make_command")
def fixture_custom_make_command(tmp_path: pathlib.Path) -> pathlib.Path:
    """Fixture generating an executable script to replace make."""
    script_path = tmp_path / "custom_make.sh"
    with script_path.open("wt", encoding="utf-8") as script_file:
        script_file.write("#!/usr/bin/env bash\n")
        script_file.write("echo 'This is a custom CMake command'\n")
    script_path.chmod(script_path.stat().st_mode | stat.S_IEXEC)
    return script_path


@pytest.fixture()
def conan_recipe_invalid(tmp_path: pathlib.Path) -> pathlib.Path:
    """Return an invalid path to a recipe."""
    return tmp_path / "does_not_exist.py"


@pytest.fixture(name="_installed_hook")
def fixture_installed_hook(conan_local_cache: typing.Dict[str, str]) -> pathlib.Path:
    """Fixture that installs a hook into the local cache."""
    if CONAN_MAJOR_VERSION == 1:
        hook_path = (
            pathlib.Path(conan_local_cache["_REAL_CONAN_LOCAL_CACHE_DIR"])
            / "hooks"
            / "my_hook.py"
        )
    else:
        hook_path = (
            pathlib.Path(conan_local_cache["_REAL_CONAN_LOCAL_CACHE_DIR"])
            / "extensions"
            / "hooks"
            / "my_hook.py"
        )
    hook_path.parent.mkdir(parents=True)
    with hook_path.open("wt", encoding="utf-8") as hook_file:
        hook_file.write("# a hook\n")
    return hook_path


@pytest.fixture()
def _conandata(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create and return path to a conandata.yml file."""
    conandata_path = tmp_path / "conandata.yml"
    content = {"versions": {"3.4.5": [1, 2, 3]}}
    with conandata_path.open("wt", encoding="utf-8") as conandata_file:
        yaml.dump(content, conandata_file)
    return conandata_path


@pytest.fixture()
def conan_dependent_recipes(
    tmp_path: pathlib.Path,
) -> typing.Tuple[pathlib.Path, str, str, pathlib.Path, str, str]:
    """Create and return dependent recipes."""
    base_name = "base"
    base_version = "1.0"
    base_recipe_path = tmp_path / "conanfile_base.py"
    with base_recipe_path.open("wt", encoding="utf-8") as conanfile:
        if CONAN_MAJOR_VERSION == 1:
            conanfile.write("from conans import ConanFile\n")
            conanfile.write("class BaseConanFile(ConanFile):\n")
        else:
            conanfile.write("from conan import ConanFile\n")
            conanfile.write("class BaseConanFile(ConanFile):\n")
        conanfile.write(f"  name = '{base_name}'\n")
        conanfile.write(f"  version = '{base_version}'\n")
        conanfile.write("  options = {'shared': [True, False]}\n")
        conanfile.write("  default_options = {'shared': True}\n")

    dependent_name = "dependent"
    dependent_version = "2.0"
    dependent_recipe_path = tmp_path / "conanfile_dependent.py"
    with dependent_recipe_path.open("wt", encoding="utf-8") as conanfile:
        if CONAN_MAJOR_VERSION == 1:
            conanfile.write("from conans import ConanFile\n")
            conanfile.write("class DependentConanFile(ConanFile):\n")
        else:
            conanfile.write("from conan import ConanFile\n")
            conanfile.write("class DependentConanFile(ConanFile):\n")
        conanfile.write(f"  name = '{dependent_name}'\n")
        conanfile.write(f"  version = '{dependent_version}'\n")
        conanfile.write("  options = {'shared': [True, False]}\n")
        conanfile.write("  default_options = {'shared': True}\n")
        if CONAN_VERSION_COMPONENTS > (1, 17, 1):
            conanfile.write(f"  requires = '{base_name}/{base_version}'\n")
        else:
            # older Conans insist on having a user and channel
            conanfile.write(
                f"  requires = '{base_name}/{base_version}@test_user/test_channel'\n"
            )

    return (
        base_recipe_path,
        base_name,
        base_version,
        dependent_recipe_path,
        dependent_name,
        dependent_version,
    )


@pytest.fixture()
def conan_testpackage_recipe(
    tmp_path: pathlib.Path, conan_recipe_name: str
) -> pathlib.Path:
    """Create and return path to a Conan test_package recipe."""
    recipe_path = tmp_path / "test_package" / "conanfile.py"
    recipe_path.parent.mkdir(parents=True)
    with recipe_path.open("wt", encoding="utf-8") as conanfile:
        if CONAN_MAJOR_VERSION == 1:
            conanfile.write("from conans import ConanFile\n")
            conanfile.write("class TestPackageConanFile(ConanFile):\n")
        else:
            conanfile.write("from conan import ConanFile\n")
            conanfile.write("class TestPackageConanFile(ConanFile):\n")
        conanfile.write(f"  name = '{conan_recipe_name}_test'\n")
        conanfile.write("  def test(self):\n")
        conanfile.write("    pass\n")
        if CONAN_MAJOR_VERSION == 2:
            conanfile.write("  def requirements(self):\n")
            conanfile.write("    self.requires(self.tested_reference_str)\n")
    return recipe_path
