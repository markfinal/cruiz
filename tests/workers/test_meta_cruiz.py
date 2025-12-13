"""Test the cruiz meta worker functionality."""

from __future__ import annotations

import typing

from cruizlib.exceptions import MetaCommandFailureError
from cruizlib.globals import CONAN_MAJOR_VERSION, CONAN_VERSION_COMPONENTS

if typing.TYPE_CHECKING:
    from unittest.mock import MagicMock

    from cruizlib.commands.metarequestconaninvocation import MetaRequestConanInvocation


def test_meta_get_version(
    cruiz_meta: typing.Tuple[MetaRequestConanInvocation, MagicMock],
) -> None:
    """Via the meta worker: Get the version."""
    meta_request, _ = cruiz_meta
    reply_payload, reply_exception = meta_request.request_data("version")
    if CONAN_MAJOR_VERSION == 1:
        assert reply_exception is None
        assert isinstance(reply_payload, str)
        assert reply_payload == ".".join([str(i) for i in CONAN_VERSION_COMPONENTS])
    else:
        assert reply_payload is None
        assert isinstance(reply_exception, MetaCommandFailureError)
        assert reply_exception.exception_type_name == "ValueError"
        assert str(reply_exception).startswith('("Meta command request not implemented')


def test_meta_stdout(
    cruiz_meta: typing.Tuple[MetaRequestConanInvocation, MagicMock],
) -> None:
    """Via the meta worker: Test stdout messages."""
    meta_request, log_details_mock = cruiz_meta
    reply_payload, _ = meta_request.request_data("test_stdout")
    assert reply_payload is None
    log_details_mock.stdout.assert_called_once_with("Testing Stdout messaging")


def test_meta_stderr(
    cruiz_meta: typing.Tuple[MetaRequestConanInvocation, MagicMock],
) -> None:
    """Via the meta worker: Test stderr messages."""
    meta_request, log_details_mock = cruiz_meta
    reply_payload, _ = meta_request.request_data("test_stderr")
    assert reply_payload is None
    log_details_mock.stderr.assert_called_once_with("Testing Stderr messaging")


def test_meta_conanlogmessage(
    cruiz_meta: typing.Tuple[MetaRequestConanInvocation, MagicMock],
) -> None:
    """Via the meta worker: Test ConanLog messages."""
    meta_request, log_details_mock = cruiz_meta
    reply_payload, _ = meta_request.request_data("test_conanlog")
    assert reply_payload is None
    log_details_mock.conan_log.assert_called_once_with("Testing ConanLog messaging")
