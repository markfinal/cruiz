"""Common fixtures for workers."""

import contextlib
import logging
import multiprocessing
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

# pylint: disable=wrong-import-order
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
def single_process_command_runner(
    request: pytest.FixtureRequest,
) -> typing.Generator[typing.List[Message], None, None]:
    """
    Fixture for running a command in the current process.

    A queue is spawned on a thread.
    The worker is executed on the test thread.
    Success/Fail responses are returned from the fixture.
    Logging responses are sent to the logger.
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

    @contextlib.contextmanager
    def _reply_queue_manager(
        reply_queue: queue.Queue[Message],
    ) -> typing.Generator[typing.List[Message], None, None]:
        replies: typing.List[Message] = []
        watcher_thread = threading.Thread(
            target=_reply_watcher, args=(reply_queue, replies)
        )
        watcher_thread.start()
        yield replies
        watcher_thread.join()

    cmd_name, worker = request.param
    params = CommandParameters(cmd_name, worker)
    reply_queue = queue.Queue[Message]()
    with _reply_queue_manager(reply_queue) as replies:
        # abusing the type system, as the API used for queue.Queue is the same
        # as for multiprocessing.Queue
        worker(reply_queue, params)
    yield replies
