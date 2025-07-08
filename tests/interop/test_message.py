"""Tests for messages."""

import cruizlib.interop.message


def test_message_extraction() -> None:
    """Message type extraction."""
    stdout = cruizlib.interop.message.Stdout("This is stdout")
    assert stdout.message == "This is stdout"

    stderr = cruizlib.interop.message.Stderr("This is stderr")
    assert stderr.message == "This is stderr"

    log = cruizlib.interop.message.ConanLogMessage("This is ConanLogMessage")
    assert log.message == "This is ConanLogMessage"

    success = cruizlib.interop.message.Success(1)
    assert isinstance(success.payload, int)
    assert success.payload == 1

    failure = cruizlib.interop.message.Failure(RuntimeError("This Failed"))
    assert isinstance(failure.exception, RuntimeError)
    assert str(failure.exception) == "This Failed"
