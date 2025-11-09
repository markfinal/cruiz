"""Tests for messages."""

import traceback

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

    try:
        raise RuntimeError("This Failed")
    except RuntimeError as exc:
        failure = cruizlib.interop.message.Failure(
            str(exc), type(exc).__name__, traceback.format_tb(exc.__traceback__)
        )
        assert failure.message == "This Failed"
        assert failure.exception_type_name == "RuntimeError"
        assert len(failure.exception_traceback) > 0
