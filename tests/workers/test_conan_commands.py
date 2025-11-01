"""Test the Conan command functionality, using multiple processes."""

import typing

import cruizlib.workers.api as workers_api
from cruizlib.interop.message import Failure, Message

import pytest


@pytest.mark.parametrize(
    "multi_process_command_runner",
    [("install", workers_api.install.invoke)],
    indirect=["multi_process_command_runner"],
)
def test_expected_failure(multi_process_command_runner: typing.List[Message]) -> None:
    """Test: running conan install incorrect setup, so has an expected failure."""
    replies = multi_process_command_runner
    assert replies
    assert isinstance(replies[0], Failure)
