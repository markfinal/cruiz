"""Common fixtures for workers."""

from __future__ import annotations

import logging
import multiprocessing
import pathlib
import queue
import threading
import typing

import cruizlib.workers.api as workers_api
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

if typing.TYPE_CHECKING:
    from cruizlib.multiprocessingmessagequeuetype import (
        MultiProcessingMessageQueueType,
    )

# pylint: disable=wrong-import-order, wrong-import-position
import pytest

LOGGER = logging.getLogger(__name__)


# TODO: unable to write the return type I'm interested in, as Python keeps erroring
# see where this fixture is used for the type intented
@pytest.fixture()
def meta() -> typing.Generator[typing.Tuple[typing.Any, typing.Any], None, None]:
    """
    Fixture for setup and teardown of meta processes and queues.

    On the test process, a request and reply queue are created.
    And then a subprocess running the worker is started.

    On teardown, the request queue is finished, and joined.
    Then the responses are joined.

    Finally the subprocess is joined.
    """
    params = CommandParameters("meta", workers_api.meta.invoke)
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


@pytest.fixture()
def reply_queue_fixture() -> (
    typing.Tuple[queue.Queue[Message], typing.List[Message], threading.Thread]
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
            if isinstance(reply, (Success, Failure)):
                replies.append(reply)
                break
            if isinstance(reply, (ConanLogMessage, Stdout, Stderr)):
                LOGGER.info("Message: '%s'", reply.message)
                continue
            raise ValueError(f"Unknown reply of type '{type(reply)}'")

    reply_queue = queue.Queue[Message]()
    replies: typing.List[Message] = []
    watcher_thread = threading.Thread(
        target=_reply_watcher, args=(reply_queue, replies)
    )
    watcher_thread.start()
    return reply_queue, replies, watcher_thread


@pytest.fixture()
def multiprocess_reply_queue_fixture() -> typing.Tuple[
    MultiProcessingMessageQueueType,
    typing.List[Message],
    threading.Thread,
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
                if isinstance(reply, (Success, Failure)):
                    replies.append(reply)
                    break
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
    watcher_thread = threading.Thread(
        target=_reply_watcher, args=(reply_queue, replies)
    )
    watcher_thread.start()
    return reply_queue, replies, watcher_thread, context


@pytest.fixture()
def conan1_recipe(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create and return path to a Conan 1 recipe."""
    recipe_path = tmp_path / "conanfile.py"
    with open(recipe_path, "wt", encoding="utf-8") as conanfile:
        conanfile.write("from conans import ConanFile\n")
        conanfile.write("class TestConanFile(ConanFile):\n")
        conanfile.write("  name = 'test'\n")
    return recipe_path
