"""Tests for plain old data."""

import pathlib
import urllib.parse

from cruizlib.interop.pod import ConanHook, ConanRemote

import pytest


def test_pod_hook_invariant_after_serialization() -> None:
    """
    Conan hooks need to serialise and deserialise.

    ConanHook objects are passed over multiprocessing via encoded URLs
    which need to be deserialized in the child process.
    """
    hook = ConanHook(pathlib.Path(__file__), True)
    args = {"hooks": hook}
    encoded = urllib.parse.urlencode(args, doseq=True)
    decoded = urllib.parse.parse_qs(encoded)
    hook_deserialized = ConanHook.from_string(decoded["hooks"][0])
    assert hook_deserialized.path == hook.path
    assert hook_deserialized.enabled == hook.enabled


def test_pod_has_path() -> None:
    """Conan hook can test whether a path is used or not."""
    path = pathlib.Path(__file__)
    hook = ConanHook(path, True)
    assert hook.has_path(path)
    assert not hook.has_path(pathlib.Path.cwd())


def test_pod_remote_invariant_after_serialization() -> None:
    """
    Conan remotes need to serialise and deserialise.

    ConanRemote objects are passed over multiprocessing via encoded URLs
    which need to be deserialized in the child process.
    """
    incorrect_prefix = "ConanRemote["
    with pytest.raises(AssertionError, match="Incorrect prefix"):
        ConanRemote.from_string(incorrect_prefix)
    incorrect_suffix = "ConanRemote(]"
    with pytest.raises(AssertionError, match="Incorrect suffix"):
        ConanRemote.from_string(incorrect_suffix)
    incorrect_args = "ConanRemote(1,2)"
    with pytest.raises(AssertionError, match="Incorrect ConanRemote argument count"):
        ConanRemote.from_string(incorrect_args)
    full_string_bad_bool = "ConanRemote(name='ABC',url='DEF',enabled='notabool')"
    with pytest.raises(ValueError):
        ConanRemote.from_string(full_string_bad_bool)
    full_string = "ConanRemote(name='ABC',url='DEF',enabled=True)"
    contrived_remote = ConanRemote.from_string(full_string)
    assert contrived_remote.name == "ABC"
    assert contrived_remote.url == "DEF"
    assert contrived_remote.enabled

    remote = ConanRemote("ABC", "DEF", False)
    args = {"remote": remote}
    encoded = urllib.parse.urlencode(args, doseq=True)
    decoded = urllib.parse.parse_qs(encoded)
    remote_deserialized = ConanRemote.from_string(decoded["remote"][0])
    assert remote_deserialized.name == remote.name
    assert remote_deserialized.url == remote.url
    assert remote_deserialized.enabled == remote.enabled
