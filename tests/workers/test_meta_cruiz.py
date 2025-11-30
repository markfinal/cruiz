"""Test the cruiz meta worker functionality."""

from __future__ import annotations

import typing

from cruizlib.exceptions import MetaCommandFailureError
from cruizlib.globals import CONAN_MAJOR_VERSION, CONAN_VERSION_COMPONENTS

if typing.TYPE_CHECKING:
    from cruizlib.workers.metarequestconaninvocation import MetaRequestConanInvocation


def test_meta_get_version(cruiz_meta: MetaRequestConanInvocation) -> None:
    """Via the meta worker: Get the version."""
    reply_payload, reply_exception = cruiz_meta.request_data("version", None)
    if CONAN_MAJOR_VERSION == 1:
        assert reply_exception is None
        assert isinstance(reply_payload, str)
        assert reply_payload == ".".join([str(i) for i in CONAN_VERSION_COMPONENTS])
    else:
        assert reply_payload is None
        assert isinstance(reply_exception, MetaCommandFailureError)
        assert reply_exception.exception_type_name == "ValueError"
        assert str(reply_exception).startswith('("Meta command request not implemented')
