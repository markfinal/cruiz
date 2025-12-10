"""
Test the conan remote package_id search functionality, in a single process.

Note that this is not how cruiz tends to work, and should be using multiple processes
to isolate the Conan commands, but this test shows it still works without that
added complexity.
"""

from __future__ import annotations

import logging
import typing
from contextlib import nullcontext as does_not_raise

import cruizlib.workers.api as workers_api
from cruizlib.globals import CONAN_MAJOR_VERSION, CONAN_VERSION_COMPONENTS
from cruizlib.interop.message import Success
from cruizlib.interop.packageidparameters import PackageIdParameters

# pylint: disable=wrong-import-order
import pytest

import texceptions

if typing.TYPE_CHECKING:
    from ttypes import RunWorkerFixture, SingleprocessReplyQueueFixture


LOGGER = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "envvars,expectation",
    [
        pytest.param(
            {"CONAN_REVISIONS_ENABLED": "0"},
            pytest.raises(texceptions.FailedMessageTestError),
            marks=pytest.mark.xfail(
                CONAN_MAJOR_VERSION == 2,
                reason="Conan 2 does not allow disabling revisions",
                strict=True,
            ),
        ),
        pytest.param(
            {"CONAN_REVISIONS_ENABLED": "1"},
            does_not_raise(),
            marks=pytest.mark.xfail(
                CONAN_VERSION_COMPONENTS == (1, 17, 1),
                reason="Conan 1.17.1 cannot connect",
                strict=True,
            ),
        ),
    ],
)
def test_conan_remote_package_id_search(
    reply_queue_fixture: SingleprocessReplyQueueFixture,
    run_worker: RunWorkerFixture,
    conan_local_cache: typing.Dict[str, str],
    envvars: typing.Dict[str, str],
    expectation: typing.ContextManager[None],
) -> None:
    """Test: running conan remote pacage_id searches for a given package."""
    worker = workers_api.packagedetails.invoke
    params = PackageIdParameters(
        reference="zlib/1.3.1#f52e03ae3d251dec704634230cd806a2",
        remote_name="conancenter",
    )
    params.added_environment = conan_local_cache
    params.added_environment.update(envvars)
    reply_queue, replies, watcher_thread, context = reply_queue_fixture()
    with expectation:
        run_worker(worker, reply_queue, params, watcher_thread, context)

        assert replies
        assert isinstance(replies[0], Success)
        assert isinstance(replies[0].payload, list)
        assert replies[0].payload
        assert "id" in replies[0].payload[0]
        assert "options" in replies[0].payload[0]
        assert "settings" in replies[0].payload[0]
        if CONAN_MAJOR_VERSION == 1:
            assert "requires" in replies[0].payload[0]
        else:
            # I suspect Conan 2 trims empty lists as zlib has no dependencies
            pass
