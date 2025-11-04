"""Test the meta worker functionality."""

from __future__ import annotations

import logging
import os
import pathlib
import typing
import urllib.parse

from cruizlib.globals import CONAN_FULL_VERSION, CONAN_MAJOR_VERSION
from cruizlib.interop.message import (
    ConanLogMessage,
    Failure,
    Message,
    Stderr,
    Stdout,
    Success,
)
from cruizlib.interop.pod import ConanRemote

# pylint: disable=wrong-import-order
import pytest

# pylint: disable=import-error,wrong-import-order
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
            raise testexceptions.FailedMessageTestError() from reply.exception
        if isinstance(reply, (ConanLogMessage, Stdout, Stderr)):
            LOGGER.info("Message: '%s'", reply.message)
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
        assert reply.payload == CONAN_FULL_VERSION
    else:
        with pytest.raises(testexceptions.FailedMessageTestError) as exc_info:
            _process_replies(reply_queue)
        assert isinstance(exc_info.value.__cause__, Exception)
        assert str(exc_info.value.__cause__).startswith(
            "Meta command request not implemented"
        )

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
                CONAN_FULL_VERSION == "1.17.1",
                reason="Unexpected Conan 1.17.1 expects user and channel",
            ),
        ),
        pytest.param(
            "mypackage/1.0.0",
            "1234",
            "5678",
            True,
            marks=pytest.mark.xfail(
                CONAN_FULL_VERSION == "1.17.1",
                reason="Unexpected Conan 1.17.1 expects user and channel",
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
)
@pytest.mark.parametrize(
    "pkgref,short_paths",
    [
        pytest.param(
            "mypackage/1.0.0",
            False,
            marks=pytest.mark.xfail(
                CONAN_FULL_VERSION == "1.17.1",
                reason="Unexpected Conan 1.17.1 expects user and channel",
            ),
        ),
        pytest.param(
            "mypackage/1.0.0",
            True,
            marks=pytest.mark.xfail(
                CONAN_FULL_VERSION == "1.17.1",
                reason="Unexpected Conan 1.17.1 expects user and channel",
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
