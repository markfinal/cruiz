"""Test the cruiz meta worker functionality."""

from __future__ import annotations

import typing

from cruizlib.globals import CONAN_VERSION_COMPONENTS

if typing.TYPE_CHECKING:
    from cruizlib.workers.metarequestconaninvocation import MetaRequestConanInvocation


def test_meta_get_version(cruiz_meta: MetaRequestConanInvocation) -> None:
    """Via the meta worker: Get the version."""
    reply_payload, _ = cruiz_meta.request_data("version", None)
    assert isinstance(reply_payload, str)
    assert reply_payload == ".".join([str(i) for i in CONAN_VERSION_COMPONENTS])
