"""Test the meta worker functionality."""

import multiprocessing
import typing

import cruizlib.workers.api as workers_api
from cruizlib.globals import CONAN_FULL_VERSION, CONAN_MAJOR_VERSION
from cruizlib.interop.commandparameters import CommandParameters
from cruizlib.interop.message import Failure, Success

import pytest


@pytest.fixture()
def meta() -> typing.Any:
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


def test_meta_get_version(meta: typing.Any) -> None:
    """Via the meta worker: Get the version."""
    request_queue = meta[0]
    reply_queue = meta[1]

    request_queue.put("version")
    request_queue.join()
    reply = reply_queue.get()
    assert reply_queue.empty()

    if CONAN_MAJOR_VERSION == 1:
        assert isinstance(reply, Success)
        assert isinstance(reply.payload, str)
        assert reply.payload == CONAN_FULL_VERSION
    else:
        assert isinstance(reply, Failure)
        assert isinstance(reply.exception, Exception)
        assert str(reply.exception).startswith("Meta command request not implemented")
