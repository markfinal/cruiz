"""Test the meta worker functionality."""

# pylint: disable=too-many-lines

from __future__ import annotations

import logging
import os
import pathlib
import typing
import urllib.parse
from contextlib import nullcontext as does_not_raise

from cruizlib.globals import CONAN_MAJOR_VERSION, CONAN_VERSION_COMPONENTS
from cruizlib.interop.message import (
    ConanLogMessage,
    Failure,
    Message,
    Stderr,
    Stdout,
    Success,
)
from cruizlib.interop.pod import ConanHook, ConanRemote

# pylint: disable=wrong-import-order
import pytest

import testexceptions

if typing.TYPE_CHECKING:
    from cruizlib.multiprocessingmessagequeuetype import (
        MultiProcessingMessageQueueType,
        MultiProcessingStringJoinableQueueType,
    )

LOGGER = logging.getLogger(__name__)


def _process_replies(reply_queue: MultiProcessingMessageQueueType) -> Message:
    while True:
        reply = reply_queue.get()
        if isinstance(reply, Success):
            break
        if isinstance(reply, Failure):
            raise testexceptions.FailedMessageTestError(
                reply.message or "<Empty message from upstream>",
                reply.exception_type_name,
                reply.exception_traceback,
            )
        if isinstance(reply, (ConanLogMessage, Stdout, Stderr)):
            LOGGER.info(reply.message)
            continue
        raise ValueError(f"Unknown reply of type '{type(reply)}'")
    return reply


def _meta_done(
    request_queue: MultiProcessingStringJoinableQueueType,
    reply_queue: MultiProcessingMessageQueueType,
) -> None:
    request_queue.join()
    reply_queue.close()
    reply_queue.join_thread()


def test_meta_get_version(
    meta: typing.Tuple[
        MultiProcessingStringJoinableQueueType, MultiProcessingMessageQueueType
    ],
) -> None:
    """Via the meta worker: Get the version."""
    request_queue, reply_queue = meta

    request_queue.put("version")

    if CONAN_MAJOR_VERSION == 1:
        reply = _process_replies(reply_queue)
        assert reply_queue.empty()
        assert isinstance(reply, Success)
        assert isinstance(reply.payload, str)
        assert reply.payload == ".".join([str(i) for i in CONAN_VERSION_COMPONENTS])
    else:
        with pytest.raises(testexceptions.FailedMessageTestError) as exc_info:
            _process_replies(reply_queue)
        assert exc_info.value.exception_type_name == "ValueError"
        assert str(exc_info.value).startswith('("Meta command request not implemented')

    _meta_done(request_queue, reply_queue)


def test_meta_get_remotes_list(
    meta: typing.Tuple[
        MultiProcessingStringJoinableQueueType, MultiProcessingMessageQueueType
    ],
) -> None:
    """Via the meta worker: Get the remotes list."""
    request_queue, reply_queue = meta

    request_queue.put("remotes_list")

    reply = _process_replies(reply_queue)
    assert reply_queue.empty()

    assert isinstance(reply, Success)
    assert isinstance(reply.payload, list)

    _meta_done(request_queue, reply_queue)


def test_meta_remotes_sync(
    meta: typing.Tuple[
        MultiProcessingStringJoinableQueueType, MultiProcessingMessageQueueType
    ],
) -> None:
    """Via the meta worker: Synchronize remotes."""
    request_queue, reply_queue = meta

    def _get_remotes() -> typing.List[ConanRemote]:
        request_queue.put("remotes_list")

        reply = _process_replies(reply_queue)
        assert isinstance(reply, Success)
        return reply.payload

    initial_remotes = _get_remotes()
    assert len(initial_remotes) == 1

    def _sync_new_remotes() -> None:
        new_remotes = [
            ConanRemote("ARemote", "http://a.remote.com", True),
            ConanRemote("BRemote", "http://b.remote.com", False),
        ]
        payload = {"remotes": new_remotes}
        remotes_sync_request = (
            f"remotes_sync?{urllib.parse.urlencode(payload, doseq=True)}"
        )

        request_queue.put(remotes_sync_request)

        reply = _process_replies(reply_queue)
        assert isinstance(reply, Success)
        assert reply.payload is None

    _sync_new_remotes()

    syncd_remotes = _get_remotes()
    assert len(syncd_remotes) == 2

    _meta_done(request_queue, reply_queue)


def test_meta_get_profiles_dir(
    meta: typing.Tuple[
        MultiProcessingStringJoinableQueueType, MultiProcessingMessageQueueType
    ],
) -> None:
    """
    Via the meta worker: Get the profiles directory.

    As this executes on an existing local cache, first get the existing profiles dir.

    Then rename that profiles dir, and re-run the query, which will force the default
    profile to be created. This emulates running this query referring to a local cache
    directory that has yet to be populated.
    """
    request_queue, reply_queue = meta

    request_queue.put("profiles_dir")

    reply = _process_replies(reply_queue)
    assert reply_queue.empty()

    assert isinstance(reply, Success)
    assert isinstance(reply.payload, pathlib.Path)

    profile_dir = reply.payload
    profile_dir.rename(profile_dir.parent / "_renamed_to_force_recreation")

    request_queue.put("profiles_dir")

    reply = _process_replies(reply_queue)
    assert reply_queue.empty()

    assert isinstance(reply, Success)
    assert reply.payload == profile_dir

    _meta_done(request_queue, reply_queue)


@pytest.mark.xfail(
    CONAN_MAJOR_VERSION == 2,
    reason="Meta get default profile path not implemented in Conan 2",
    strict=True,
)
def test_meta_get_default_profile_path(
    meta: typing.Tuple[
        MultiProcessingStringJoinableQueueType, MultiProcessingMessageQueueType
    ],
) -> None:
    """Via the meta worker: Get the default profile path."""
    request_queue, reply_queue = meta

    request_queue.put("default_profile_path")

    reply = _process_replies(reply_queue)
    assert reply_queue.empty()

    assert isinstance(reply, Success)
    assert isinstance(reply.payload, str)

    _meta_done(request_queue, reply_queue)


def test_meta_get_profile_meta(
    meta: typing.Tuple[
        MultiProcessingStringJoinableQueueType, MultiProcessingMessageQueueType
    ],
    conanised_os: str,
) -> None:
    """Via the meta worker: Get profile meta."""
    request_queue, reply_queue = meta

    payload = {"name": "default"}
    get_profile_meta_request = (
        f"profile_meta?{urllib.parse.urlencode(payload, doseq=True)}"
    )
    request_queue.put(get_profile_meta_request)

    reply = _process_replies(reply_queue)
    _meta_done(request_queue, reply_queue)
    assert reply_queue.empty()
    assert isinstance(reply, Success)
    assert isinstance(reply.payload, dict)
    settings_meta = reply.payload["settings"]
    assert "os" in settings_meta
    assert settings_meta["os"] == conanised_os


def _pkgref_components(
    _pkgref: str,
) -> typing.Tuple[str, str, typing.Optional[str], typing.Optional[str]]:
    try:
        nameversion, userchannel = _pkgref.split("@")
        name, version = nameversion.split("/")
        user, channel = userchannel.split("/")
    except ValueError:
        name, version = _pkgref.split("/")
        user, channel = "_", "_"
    return name, version, user, channel


@pytest.mark.xfail(
    CONAN_MAJOR_VERSION == 2,
    reason="Meta get package dir not implemented in Conan 2",
    strict=True,
)
@pytest.mark.parametrize(
    "pkgref,package_id,rrev,short_paths",
    [
        pytest.param(
            "mypackage/1.0.0",
            "1234",
            "5678",
            False,
            marks=pytest.mark.xfail(
                CONAN_VERSION_COMPONENTS == (1, 17, 1),
                reason="Unexpected Conan 1.17.1 expects user and channel",
                strict=True,
            ),
        ),
        pytest.param(
            "mypackage/1.0.0",
            "1234",
            "5678",
            True,
            marks=pytest.mark.xfail(
                CONAN_VERSION_COMPONENTS == (1, 17, 1),
                reason="Unexpected Conan 1.17.1 expects user and channel",
                strict=True,
            ),
        ),
        ("mypackage/1.0.0@cruiz/stable", "1234", "5678", False),
        ("mypackage/1.0.0@cruiz/stable", "1234", "5678", True),
    ],
)
def test_meta_get_package_dir(
    meta: typing.Tuple[
        MultiProcessingStringJoinableQueueType, MultiProcessingMessageQueueType
    ],
    pkgref: str,
    package_id: str,
    rrev: str,
    short_paths: bool,
) -> None:
    """Via the meta worker: Get the directory of a package."""
    request_queue, reply_queue = meta

    payload = {
        "ref": pkgref,
        "package_id": package_id,
        "revision": rrev,
        "short_paths": short_paths,
    }
    get_profile_meta_request = (
        f"package_dir?{urllib.parse.urlencode(payload, doseq=True)}"
    )
    request_queue.put(get_profile_meta_request)

    reply = _process_replies(reply_queue)
    _meta_done(request_queue, reply_queue)
    assert reply_queue.empty()
    assert isinstance(reply, Success)
    assert isinstance(reply.payload, pathlib.Path)

    if CONAN_MAJOR_VERSION == 1:
        name, version, user, channel = _pkgref_components(pkgref)
        assert os.fspath(reply.payload).endswith(
            f".conan/data/{name}/{version}/{user}/{channel}/package/{package_id}"
        )


@pytest.mark.xfail(
    CONAN_MAJOR_VERSION == 2,
    reason="Meta get package export dir not implemented in Conan 2",
    strict=True,
)
@pytest.mark.parametrize(
    "pkgref,short_paths",
    [
        pytest.param(
            "mypackage/1.0.0",
            False,
            marks=pytest.mark.xfail(
                CONAN_VERSION_COMPONENTS == (1, 17, 1),
                reason="Unexpected Conan 1.17.1 expects user and channel",
                strict=True,
            ),
        ),
        pytest.param(
            "mypackage/1.0.0",
            True,
            marks=pytest.mark.xfail(
                CONAN_VERSION_COMPONENTS == (1, 17, 1),
                reason="Unexpected Conan 1.17.1 expects user and channel",
                strict=True,
            ),
        ),
        ("mypackage/1.0.0@cruiz/stable", False),
        ("mypackage/1.0.0@cruiz/stable", True),
    ],
)
def test_meta_get_package_export_dir(
    meta: typing.Tuple[
        MultiProcessingStringJoinableQueueType, MultiProcessingMessageQueueType
    ],
    pkgref: str,
    short_paths: bool,
) -> None:
    """Via the meta worker: Get the export directory of a package."""
    request_queue, reply_queue = meta

    payload = {
        "ref": pkgref,
        "short_paths": short_paths,
    }
    get_profile_meta_request = (
        f"package_export_dir?{urllib.parse.urlencode(payload, doseq=True)}"
    )
    request_queue.put(get_profile_meta_request)

    reply = _process_replies(reply_queue)
    _meta_done(request_queue, reply_queue)
    assert reply_queue.empty()
    assert isinstance(reply, Success)
    assert isinstance(reply.payload, pathlib.Path)

    if CONAN_MAJOR_VERSION == 1:
        name, version, user, channel = _pkgref_components(pkgref)
        assert os.fspath(reply.payload).endswith(
            f".conan/data/{name}/{version}/{user}/{channel}/export"
        )


@pytest.mark.xfail(
    CONAN_MAJOR_VERSION == 2,
    reason="Meta get export sources dir not implemented in Conan 2",
    strict=True,
)
@pytest.mark.parametrize(
    "pkgref,short_paths",
    [
        pytest.param(
            "mypackage/1.0.0",
            False,
            marks=pytest.mark.xfail(
                CONAN_VERSION_COMPONENTS == (1, 17, 1),
                reason="Unexpected Conan 1.17.1 expects user and channel",
                strict=True,
            ),
        ),
        pytest.param(
            "mypackage/1.0.0",
            True,
            marks=pytest.mark.xfail(
                CONAN_VERSION_COMPONENTS == (1, 17, 1),
                reason="Unexpected Conan 1.17.1 expects user and channel",
                strict=True,
            ),
        ),
        ("mypackage/1.0.0@cruiz/stable", False),
        ("mypackage/1.0.0@cruiz/stable", True),
    ],
)
def test_meta_get_package_export_sources_dir(
    meta: typing.Tuple[
        MultiProcessingStringJoinableQueueType, MultiProcessingMessageQueueType
    ],
    pkgref: str,
    short_paths: bool,
) -> None:
    """Via the meta worker: Get the export sources directory of a package."""
    request_queue, reply_queue = meta

    payload = {
        "ref": pkgref,
        "short_paths": short_paths,
    }
    get_profile_meta_request = (
        f"package_export_sources_dir?{urllib.parse.urlencode(payload, doseq=True)}"
    )
    request_queue.put(get_profile_meta_request)

    reply = _process_replies(reply_queue)
    _meta_done(request_queue, reply_queue)
    assert reply_queue.empty()
    assert isinstance(reply, Success)
    assert isinstance(reply.payload, pathlib.Path)

    if CONAN_MAJOR_VERSION == 1:
        name, version, user, channel = _pkgref_components(pkgref)
        assert os.fspath(reply.payload).endswith(
            f".conan/data/{name}/{version}/{user}/{channel}/export_source"
        )


@pytest.mark.xfail(
    CONAN_MAJOR_VERSION == 2,
    reason="Meta get editable list not implemented in Conan 2",
    strict=True,
)
def test_meta_get_editable_list(
    meta: typing.Tuple[
        MultiProcessingStringJoinableQueueType, MultiProcessingMessageQueueType
    ],
) -> None:
    """Via the meta worker: Get editable list."""
    request_queue, reply_queue = meta

    request_queue.put("editable_list")

    reply = _process_replies(reply_queue)
    _meta_done(request_queue, reply_queue)
    assert reply_queue.empty()
    assert isinstance(reply, Success)
    assert isinstance(reply.payload, list)


@pytest.mark.parametrize(
    "pkgref_fixture,path_fixture,expectation",
    [
        pytest.param(
            "conan_recipe_pkgref_namespaced",
            "conan_recipe_invalid",
            pytest.raises(testexceptions.FailedMessageTestError),
        ),
        (
            "conan_recipe_pkgref_namespaced",
            "conan_recipe_invalid",
            pytest.raises(testexceptions.FailedMessageTestError),
        ),
        pytest.param(
            "conan_recipe_pkgref_namespaced",
            "conan_recipe",
            does_not_raise(),
            marks=pytest.mark.xfail(
                CONAN_MAJOR_VERSION == 2,
                reason="Expected to fail in Conan 2 as editable is not implemented",
                strict=True,
            ),
        ),
        (
            "conan_recipe_pkgref_namespaced",
            "conan_recipe_name_invalid",
            pytest.raises(testexceptions.FailedMessageTestError),
        ),
    ],
)
def test_meta_editable_add(
    meta: typing.Tuple[
        MultiProcessingStringJoinableQueueType, MultiProcessingMessageQueueType
    ],
    pkgref_fixture: str,
    path_fixture: str,
    expectation: typing.ContextManager[None],
    request: pytest.FixtureRequest,
) -> None:
    """Via the meta worker: Editable add."""
    request_queue, reply_queue = meta

    payload = {
        "ref": request.getfixturevalue(pkgref_fixture),
        "path": request.getfixturevalue(path_fixture),
    }
    meta_request = f"editable_add?{urllib.parse.urlencode(payload, doseq=True)}"
    request_queue.put(meta_request)

    # for nullcontext warning, see https://github.com/python/mypy/issues/10109
    with expectation:
        reply = _process_replies(reply_queue)
        _meta_done(request_queue, reply_queue)
        assert reply_queue.empty()
        assert isinstance(reply, Success)
        assert reply.payload is None


@pytest.mark.xfail(
    CONAN_MAJOR_VERSION == 2,
    reason="Meta editable remove not implemented in Conan 2",
    strict=True,
)
@pytest.mark.parametrize(
    "pkgref_to_add_fixture,pkgref_to_remove_fixture,path_fixture,expectation",
    [
        (
            "conan_recipe_pkgref_namespaced",
            "conan_recipe_pkgref_namespaced",
            "conan_recipe",
            True,
        ),
        (
            None,
            "conan_recipe_pkgref_namespaced",
            None,
            False,
        ),
        pytest.param(
            "conan_recipe_pkgref_namespaced",
            "conan_recipe_pkgref",
            "conan_recipe",
            False,
            marks=pytest.mark.xfail(
                CONAN_VERSION_COMPONENTS == (1, 17, 1),
                reason="Unexpected Conan 1.17.1 expects user and channel",
                strict=True,
            ),
        ),
    ],
)
# pylint: disable=too-many-arguments,too-many-positional-arguments
def test_meta_editable_remove(
    meta: typing.Tuple[
        MultiProcessingStringJoinableQueueType, MultiProcessingMessageQueueType
    ],
    pkgref_to_add_fixture: typing.Optional[str],
    pkgref_to_remove_fixture: str,
    path_fixture: str,
    expectation: bool,
    request: pytest.FixtureRequest,
) -> None:
    """Via the meta worker: Editable remove."""
    request_queue, reply_queue = meta

    # first add an editable, if provided
    if pkgref_to_add_fixture:
        pkgref_to_add = request.getfixturevalue(pkgref_to_add_fixture)
        payload = {
            "ref": pkgref_to_add,
            "path": request.getfixturevalue(path_fixture),
        }
        meta_request = f"editable_add?{urllib.parse.urlencode(payload, doseq=True)}"
        request_queue.put(meta_request)

        reply = _process_replies(reply_queue)
        assert reply_queue.empty()
        assert isinstance(reply, Success)
        assert reply.payload is None

    payload = {
        "ref": request.getfixturevalue(pkgref_to_remove_fixture),
    }
    meta_request = f"editable_remove?{urllib.parse.urlencode(payload, doseq=True)}"
    request_queue.put(meta_request)

    reply = _process_replies(reply_queue)
    assert reply_queue.empty()
    assert isinstance(reply, Success)
    assert isinstance(reply.payload, bool)
    assert reply.payload == expectation

    _meta_done(request_queue, reply_queue)


def test_meta_inspect_recipe(
    meta: typing.Tuple[
        MultiProcessingStringJoinableQueueType, MultiProcessingMessageQueueType
    ],
    conan_recipe: str,
) -> None:
    """Via the meta worker: Inspect a recipe."""
    request_queue, reply_queue = meta

    payload = {
        "path": conan_recipe,
    }
    meta_request = f"inspect_recipe?{urllib.parse.urlencode(payload, doseq=True)}"
    request_queue.put(meta_request)

    reply = _process_replies(reply_queue)
    _meta_done(request_queue, reply_queue)

    assert reply_queue.empty()
    assert isinstance(reply, Success)
    assert isinstance(reply.payload, dict)
    assert "name" in reply.payload
    assert "version" in reply.payload
    assert "options" in reply.payload
    assert "default_options" in reply.payload


@pytest.mark.xfail(
    CONAN_MAJOR_VERSION == 2,
    reason="Meta get hook path not implemented in Conan 2",
    strict=True,
)
def test_meta_get_hook_path(
    meta: typing.Tuple[
        MultiProcessingStringJoinableQueueType, MultiProcessingMessageQueueType
    ],
) -> None:
    """Via the meta worker: Get the hook path."""
    request_queue, reply_queue = meta

    request_queue.put("hook_path")

    reply = _process_replies(reply_queue)
    _meta_done(request_queue, reply_queue)

    assert reply_queue.empty()
    assert isinstance(reply, Success)
    assert isinstance(reply.payload, str)


@pytest.mark.xfail(
    CONAN_MAJOR_VERSION == 2,
    reason="Meta enabled hooks not implemented in Conan 2",
    strict=True,
)
def test_meta_enabled_hooks(
    meta: typing.Tuple[
        MultiProcessingStringJoinableQueueType, MultiProcessingMessageQueueType
    ],
) -> None:
    """Via the meta worker: Enabled hooks."""
    request_queue, reply_queue = meta

    request_queue.put("enabled_hooks")

    reply = _process_replies(reply_queue)
    _meta_done(request_queue, reply_queue)

    assert reply_queue.empty()
    assert isinstance(reply, Success)
    assert isinstance(reply.payload, bool)


@pytest.mark.xfail(
    CONAN_MAJOR_VERSION == 2,
    reason="Meta available hooks not implemented in Conan 2",
    strict=True,
)
@pytest.mark.parametrize(
    "with_hook,with_hooks_dotgit_folder,expected_hook_count",
    [
        (True, False, 1),
        (False, False, 0),
        (True, True, 1),
        (False, True, 0),
    ],
)
# pylint: disable=too-many-arguments,too-many-positional-arguments
def test_meta_available_hooks(
    meta: typing.Tuple[
        MultiProcessingStringJoinableQueueType, MultiProcessingMessageQueueType
    ],
    with_hook: bool,
    with_hooks_dotgit_folder: bool,
    expected_hook_count: int,
    conan_local_cache: typing.Dict[str, str],
    request: pytest.FixtureRequest,
) -> None:
    """Via the meta worker: Available hooks."""
    request_queue, reply_queue = meta

    if with_hook:
        request.getfixturevalue("_installed_hook")

    if with_hooks_dotgit_folder:
        local_cache_dir = pathlib.Path(conan_local_cache["_REAL_CONAN_LOCAL_CACHE_DIR"])
        (local_cache_dir / "hooks" / ".git").mkdir(parents=True)

    request_queue.put("available_hooks")

    reply = _process_replies(reply_queue)
    _meta_done(request_queue, reply_queue)

    assert reply_queue.empty()
    assert isinstance(reply, Success)
    assert isinstance(reply.payload, list)
    assert len(reply.payload) == expected_hook_count


@pytest.mark.parametrize(
    "with_hook,with_hooks_dotgit_folder,expected_hook_count",
    [
        (True, False, 1),
        (False, False, 0),
        (True, True, 1),
        (False, True, 0),
    ],
)
# pylint: disable=too-many-arguments,too-many-positional-arguments
def test_meta_get_hooks(
    meta: typing.Tuple[
        MultiProcessingStringJoinableQueueType, MultiProcessingMessageQueueType
    ],
    with_hook: bool,
    with_hooks_dotgit_folder: bool,
    expected_hook_count: int,
    conan_local_cache: typing.Dict[str, str],
    request: pytest.FixtureRequest,
) -> None:
    """Via the meta worker: Get hooks."""
    request_queue, reply_queue = meta

    if with_hook:
        request.getfixturevalue("_installed_hook")

    if with_hooks_dotgit_folder:
        local_cache_dir = pathlib.Path(conan_local_cache["_REAL_CONAN_LOCAL_CACHE_DIR"])
        if CONAN_MAJOR_VERSION == 1:
            (local_cache_dir / "hooks" / ".git").mkdir(parents=True)
        else:
            (local_cache_dir / "extensions" / "hooks" / ".git").mkdir(parents=True)

    request_queue.put("get_hooks")

    reply = _process_replies(reply_queue)
    _meta_done(request_queue, reply_queue)

    assert reply_queue.empty()
    assert isinstance(reply, Success)
    assert isinstance(reply.payload, list)
    assert len(reply.payload) == expected_hook_count
    if expected_hook_count > 0:
        assert isinstance(reply.payload[0], ConanHook)


@pytest.mark.xfail(
    CONAN_MAJOR_VERSION == 2,
    reason="Meta sync hooks not implemented in Conan 2",
    strict=True,
)
@pytest.mark.parametrize(
    "hook_path, hook_enabled",
    [
        ("enabled.py", True),
        ("disabled.py", False),
    ],
)
def test_meta_sync_hooks(
    meta: typing.Tuple[
        MultiProcessingStringJoinableQueueType, MultiProcessingMessageQueueType
    ],
    hook_path: str,
    hook_enabled: bool,
    conan_local_cache: typing.Dict[str, str],
) -> None:
    """
    Via the meta worker: Sync hooks.

    When a hook is enabled, it is subsequently disabled.
    Disabling a non-existent hook is a no-op path.

    TODO: Missing coverage for Conan config hooks managing a hook without a .py
    extension in the config but with a .py extension on disk
    """
    request_queue, reply_queue = meta

    real_hook_path = (
        pathlib.Path(conan_local_cache["_REAL_CONAN_LOCAL_CACHE_DIR"])
        / "hooks"
        / hook_path
    )
    hook = ConanHook(real_hook_path, hook_enabled)
    payload = {"hooks": [hook]}
    hooks_sync_request = f"hooks_sync?{urllib.parse.urlencode(payload, doseq=True)}"
    request_queue.put(hooks_sync_request)

    reply = _process_replies(reply_queue)

    assert reply_queue.empty()
    assert isinstance(reply, Success)
    assert reply.payload is None

    if hook.enabled:
        hook = ConanHook(hook.path, False)

    payload = {"hooks": [hook]}
    hooks_sync_request = f"hooks_sync?{urllib.parse.urlencode(payload, doseq=True)}"
    request_queue.put(hooks_sync_request)

    reply = _process_replies(reply_queue)
    _meta_done(request_queue, reply_queue)

    assert reply_queue.empty()
    assert isinstance(reply, Success)
    assert reply.payload is None


@pytest.mark.xfail(
    CONAN_MAJOR_VERSION == 2,
    reason="Meta enable hooks not implemented in Conan 2",
    strict=True,
)
def test_meta_enable_hooks(
    meta: typing.Tuple[
        MultiProcessingStringJoinableQueueType, MultiProcessingMessageQueueType
    ],
    _installed_hook: pathlib.Path,
) -> None:
    """Via the meta worker: Enable hooks."""
    request_queue, reply_queue = meta

    payload = {"hook": [_installed_hook], "hook_enabled": True}
    hooks_sync_request = f"enable_hook?{urllib.parse.urlencode(payload, doseq=True)}"
    request_queue.put(hooks_sync_request)

    reply = _process_replies(reply_queue)

    assert reply_queue.empty()
    assert isinstance(reply, Success)
    assert reply.payload is None

    payload = {"hook": [_installed_hook], "hook_enabled": False}
    hooks_sync_request = f"enable_hook?{urllib.parse.urlencode(payload, doseq=True)}"
    request_queue.put(hooks_sync_request)

    reply = _process_replies(reply_queue)

    assert reply_queue.empty()
    assert isinstance(reply, Success)
    assert reply.payload is None

    _meta_done(request_queue, reply_queue)


def test_meta_get_conandata(
    meta: typing.Tuple[
        MultiProcessingStringJoinableQueueType, MultiProcessingMessageQueueType
    ],
    conan_recipe: pathlib.Path,
    _conandata: pathlib.Path,
) -> None:
    """Via the meta worker: Get conandata."""
    request_queue, reply_queue = meta

    payload = {"path": [os.fspath(conan_recipe)]}
    hooks_sync_request = f"get_conandata?{urllib.parse.urlencode(payload, doseq=True)}"
    request_queue.put(hooks_sync_request)

    reply = _process_replies(reply_queue)
    _meta_done(request_queue, reply_queue)

    assert reply_queue.empty()
    assert isinstance(reply, Success)
    assert isinstance(reply.payload, dict)


@pytest.mark.xfail(
    CONAN_MAJOR_VERSION == 2,
    reason="Meta get CMake generator not implemented in Conan 2",
    strict=True,
)
def test_meta_get_cmake_generator(
    meta: typing.Tuple[
        MultiProcessingStringJoinableQueueType, MultiProcessingMessageQueueType
    ],
) -> None:
    """Via the meta worker: Get Conan's default CMake generator."""
    request_queue, reply_queue = meta

    request_queue.put("get_cmake_generator")

    reply = _process_replies(reply_queue)
    _meta_done(request_queue, reply_queue)

    assert reply_queue.empty()
    assert isinstance(reply, Success)
    assert reply.payload is None, "As the CMake default generator is not set"


def test_meta_get_config(
    meta: typing.Tuple[
        MultiProcessingStringJoinableQueueType, MultiProcessingMessageQueueType
    ],
) -> None:
    """Via the meta worker: Get Conan config."""
    request_queue, reply_queue = meta

    if CONAN_MAJOR_VERSION == 1:
        payload = {"config": "general.default_package_id_mode"}
    else:
        payload = {"config": "core.package_id:default_embed_mode"}
    hooks_sync_request = f"get_config?{urllib.parse.urlencode(payload, doseq=True)}"
    request_queue.put(hooks_sync_request)

    reply = _process_replies(reply_queue)
    _meta_done(request_queue, reply_queue)

    assert reply_queue.empty()
    assert isinstance(reply, Success)
    if CONAN_MAJOR_VERSION == 1:
        assert isinstance(reply.payload, str)
        assert reply.payload == "semver_direct_mode"
    else:
        assert reply.payload is None, "Conan 2 sets no default config"


def test_meta_get_config_envvars(
    meta: typing.Tuple[
        MultiProcessingStringJoinableQueueType, MultiProcessingMessageQueueType
    ],
) -> None:
    """Via the meta worker: Get Conan config environment variables."""
    request_queue, reply_queue = meta

    request_queue.put("get_config_envvars")

    reply = _process_replies(reply_queue)
    _meta_done(request_queue, reply_queue)

    assert reply_queue.empty()
    assert isinstance(reply, Success)
    assert isinstance(reply.payload, list)
    assert len(reply.payload) > 0


def test_meta_create_default_profile(
    meta: typing.Tuple[
        MultiProcessingStringJoinableQueueType, MultiProcessingMessageQueueType
    ],
) -> None:
    """Via the meta worker: Create default Conan profile."""
    request_queue, reply_queue = meta

    request_queue.put("create_default_profile")

    reply = _process_replies(reply_queue)
    _meta_done(request_queue, reply_queue)

    assert reply_queue.empty()
    assert isinstance(reply, Success)
    assert reply.payload is None


@pytest.mark.xfail(
    CONAN_MAJOR_VERSION == 2,
    reason="Meta set config not implemented in Conan 2",
    strict=True,
)
def test_meta_set_config(
    meta: typing.Tuple[
        MultiProcessingStringJoinableQueueType, MultiProcessingMessageQueueType
    ],
) -> None:
    """Via the meta worker: Set Conan config."""
    request_queue, reply_queue = meta

    payload = {"config": "general.default_package_id_mode", "value": "patch_mode"}
    set_config_request = f"set_config?{urllib.parse.urlencode(payload, doseq=True)}"
    request_queue.put(set_config_request)

    reply = _process_replies(reply_queue)
    _meta_done(request_queue, reply_queue)

    assert reply_queue.empty()
    assert isinstance(reply, Success)
    assert reply.payload is None


def test_meta_unknown_request(
    meta: typing.Tuple[
        MultiProcessingStringJoinableQueueType, MultiProcessingMessageQueueType
    ],
) -> None:
    """Via the meta worker: An unknown request."""
    request_queue, reply_queue = meta

    request_queue.put("this_is_unknown")

    with pytest.raises(testexceptions.FailedMessageTestError) as exc_info:
        _process_replies(reply_queue)
    assert exc_info.value.exception_type_name == "ValueError"
    assert str(exc_info.value).startswith('("Meta command request not implemented:')
