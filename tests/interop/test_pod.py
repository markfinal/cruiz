"""Tests for plain old data."""

import pathlib
import urllib.parse

from cruiz.interop.pod import ConanHook


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
