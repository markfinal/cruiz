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
