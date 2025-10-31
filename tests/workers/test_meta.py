"""Test the meta worker functionality."""

from __future__ import annotations

import logging
import typing

from cruizlib.globals import CONAN_FULL_VERSION, CONAN_MAJOR_VERSION
from cruizlib.interop.message import (
    ConanLogMessage,
    Failure,
    Message,
    Stderr,
    Stdout,
    Success,
)

if typing.TYPE_CHECKING:
    from cruizlib.multiprocessingmessagequeuetype import (
        MultiProcessingMessageQueueType,
        MultiProcessingStringJoinableQueueType,
    )

LOGGER = logging.getLogger(__name__)


def _process_replies(reply_queue: MultiProcessingMessageQueueType) -> Message:
    while True:
        reply = reply_queue.get()
        if isinstance(reply, (Success, Failure)):
            break
        if isinstance(reply, (ConanLogMessage, Stdout, Stderr)):
            LOGGER.info("Message: '%s'", reply.message)
            continue
        raise ValueError(f"Unknown reply of type '{type(reply)}'")
    reply_queue.close()
    reply_queue.join_thread()
    return reply


def test_meta_get_version(
    meta: typing.Tuple[
        MultiProcessingStringJoinableQueueType, MultiProcessingMessageQueueType
    ],
) -> None:
    """Via the meta worker: Get the version."""
    request_queue, reply_queue = meta

    request_queue.put("version")
    request_queue.join()

    reply = _process_replies(reply_queue)
    assert reply_queue.empty()

    if CONAN_MAJOR_VERSION == 1:
        assert isinstance(reply, Success)
        assert isinstance(reply.payload, str)
        assert reply.payload == CONAN_FULL_VERSION
    else:
        assert isinstance(reply, Failure)
        assert isinstance(reply.exception, Exception)
        assert str(reply.exception).startswith("Meta command request not implemented")


def test_meta_get_remotes_list(
    meta: typing.Tuple[
        MultiProcessingStringJoinableQueueType, MultiProcessingMessageQueueType
    ],
) -> None:
    """Via the meta worker: Get the remotes list."""
    request_queue, reply_queue = meta

    request_queue.put("remotes_list")
    request_queue.join()

    reply = _process_replies(reply_queue)
    assert reply_queue.empty()

    assert isinstance(reply, Success)
    assert isinstance(reply.payload, list)
