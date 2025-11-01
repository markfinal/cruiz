"""
Test the Conan command functionality, in a single process.

Note that this is not how cruiz tends to work, and should be using multiple processes
to isolate the Conan commands, but this test shows it still works without that
added complexity.
"""

import logging
import typing

import cruizlib.workers.api as workers_api
from cruizlib.interop.message import Failure, Message

import pytest


LOGGER = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "single_process_command_runner",
    [("install", workers_api.install.invoke)],
    indirect=["single_process_command_runner"],
)
def test_expected_failure(
    single_process_command_runner: typing.List[Message],
) -> None:
    """Test: running conan install incorrect setup, so has an expected failure."""
    replies = single_process_command_runner
    assert replies
    assert isinstance(replies[0], Failure)
