"""Common fixtures for workers."""

import multiprocessing
import typing

import cruizlib.workers.api as workers_api
from cruizlib.interop.commandparameters import CommandParameters

# pylint: disable=wrong-import-order
import pytest


# TODO: unable to write the return type I'm interested in, as Python keeps erroring
# see where this fixture is used for the type intented
@pytest.fixture()
def meta() -> typing.Generator[typing.Tuple[typing.Any, typing.Any], None, None]:
    """Fixture for setup and teardown of meta processes and queues."""
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
    request_queue.put("end")
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
