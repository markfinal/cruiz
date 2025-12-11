"""."""

from __future__ import annotations

import logging
import typing

import cruizlib.workers.api as workers_api

# pylint: disable=wrong-import-order
import pytest

import texceptions

if typing.TYPE_CHECKING:
    from ttypes import MessageReplyProcessorFixture

LOGGER = logging.getLogger(__name__)


def test_message_reply_processor_messaging(
    messagereplyprocessor_fixture: MessageReplyProcessorFixture,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Exercise messaging in the message reply processor."""
    caplog.set_level(logging.INFO)
    worker = workers_api.messagingtest.invoke
    reply_queue, replies, watcher_thread, processor, context = (
        messagereplyprocessor_fixture()
    )

    process = context.Process(target=worker, args=(reply_queue,))
    process.start()
    process.join()

    processor.stop()

    watcher_thread.wait(5)
    if not watcher_thread.isFinished():
        raise texceptions.WatcherThreadTimeoutError()

    assert "Stdout Test" in caplog.text
    assert "Stderr Test" in caplog.text
    assert "ConanLogMessage Test" in caplog.text
    assert not replies


def test_message_reply_processor_success(
    messagereplyprocessor_fixture: MessageReplyProcessorFixture,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Exercise Successful replies in the message reply processor."""
    caplog.set_level(logging.INFO)
    worker = workers_api.successtest.invoke
    reply_queue, replies, watcher_thread, processor, context = (
        messagereplyprocessor_fixture()
    )

    process = context.Process(target=worker, args=(reply_queue,))
    process.start()
    process.join()

    processor.stop()

    watcher_thread.wait(5)
    if not watcher_thread.isFinished():
        raise texceptions.WatcherThreadTimeoutError()

    assert replies
    assert len(replies) == 1
    assert isinstance(replies[0], str)
    assert replies[0] == "This was a success!"


@pytest.mark.parametrize("html", [None, "<p>A failure</p>"])
def test_message_reply_processor_failure(
    messagereplyprocessor_fixture: MessageReplyProcessorFixture,
    caplog: pytest.LogCaptureFixture,
    html: typing.Optional[str],
) -> None:
    """Exercise Failed replies in the message reply processor."""
    caplog.set_level(logging.INFO)
    worker = workers_api.failuretest.invoke
    reply_queue, replies, watcher_thread, processor, context = (
        messagereplyprocessor_fixture()
    )

    process = context.Process(target=worker, args=(reply_queue, html))
    process.start()
    process.join()

    processor.stop()

    watcher_thread.wait(5)
    if not watcher_thread.isFinished():
        raise texceptions.WatcherThreadTimeoutError()

    assert replies
    assert len(replies) == 1
    assert isinstance(replies[0], Exception)
    assert str(replies[0]) == "Failed Test!"
    if html is not None:
        assert html in caplog.text
    else:
        assert "<font color='red'>" in caplog.text


def test_message_reply_processor_unknown(
    messagereplyprocessor_fixture: MessageReplyProcessorFixture,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Exercise an unknown message in the message reply processor."""
    caplog.set_level(logging.INFO)
    worker = workers_api.unknownmessagetest.invoke
    reply_queue, replies, watcher_thread, processor, context = (
        messagereplyprocessor_fixture()
    )

    process = context.Process(target=worker, args=(reply_queue,))
    process.start()
    process.join()

    processor.stop()

    watcher_thread.wait(5)
    if not watcher_thread.isFinished():
        raise texceptions.WatcherThreadTimeoutError()

    assert not replies
    assert "Unknown message type" in caplog.text
