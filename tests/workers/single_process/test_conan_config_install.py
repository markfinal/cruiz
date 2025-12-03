"""
Test the conan config install functionality, in a single process.

Note that this is not how cruiz tends to work, and should be using multiple processes
to isolate the Conan commands, but this test shows it still works without that
added complexity.
"""

from __future__ import annotations

import logging
import os
import pathlib
import subprocess
import typing
import zipfile

import cruizlib.workers.api as workers_api
from cruizlib.globals import CONAN_MAJOR_VERSION
from cruizlib.interop.commandparameters import CommandParameters
from cruizlib.interop.message import Success

# pylint: disable=wrong-import-order
import pytest

import texceptions

if typing.TYPE_CHECKING:
    from ttypes import MultiprocessReplyQueueFixture, RunWorkerFixture


LOGGER = logging.getLogger(__name__)


def test_conan_config_install_missing(
    multiprocess_reply_queue_fixture: MultiprocessReplyQueueFixture,
    run_worker: RunWorkerFixture,
    conan_local_cache: typing.Dict[str, str],
) -> None:
    """Test: running conan config install that is missing."""
    worker = workers_api.configinstall.invoke
    params = CommandParameters("install_config", worker)
    params.added_environment = conan_local_cache
    params.named_arguments["pathOrUrl"] = "/some/unknownpath"
    reply_queue, _, watcher_thread, context = multiprocess_reply_queue_fixture()
    with pytest.raises(
        texceptions.FailedMessageTestError,
        match="Unable to deduce type config install",
    ):
        run_worker(worker, reply_queue, params, watcher_thread, context)


@pytest.fixture(name="conan_config_zip")
def fixture_conan_config_zip(tmp_path: pathlib.Path) -> pathlib.Path:
    """Fixture generating a zip file containing a Conan config."""
    config_path = tmp_path / "conan_config.zip"
    with zipfile.ZipFile(config_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("conan.conf", "[general]\n")
    return config_path


@pytest.fixture(name="conan_config_git_repo")
def fixture_conan_config_git_repo(tmp_path: pathlib.Path) -> pathlib.Path:
    """Fixture generating a local Git repo containing a Conan config."""
    config_dir = tmp_path / "conan_config"
    config_dir.mkdir(parents=True)
    subprocess.run(["git", "init", "-b", "main"], cwd=config_dir, check=True)
    subprocess.run(
        ["git", "config", "user.email", "cruiz-tests@cruiz.org"],
        cwd=config_dir,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "cruiz-tests"], cwd=config_dir, check=True
    )
    conan_config_path = config_dir / "conan.conf"
    with conan_config_path.open("wt", encoding="utf-8") as config_file:
        config_file.write("[general]\n")
    subprocess.run(["git", "add", "-A"], cwd=config_dir, check=True)
    subprocess.run(["git", "commit", "-m", "Initial files"], cwd=config_dir, check=True)
    return config_dir


def test_conan_config_install_from_zip(
    multiprocess_reply_queue_fixture: MultiprocessReplyQueueFixture,
    run_worker: RunWorkerFixture,
    conan_local_cache: typing.Dict[str, str],
    conan_config_zip: pathlib.Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test: running conan config install with a zip file."""
    caplog.set_level(logging.INFO)
    worker = workers_api.configinstall.invoke
    params = CommandParameters("install_config", worker)
    params.added_environment = conan_local_cache
    params.named_arguments["pathOrUrl"] = os.fspath(conan_config_zip)
    reply_queue, replies, watcher_thread, context = multiprocess_reply_queue_fixture()
    run_worker(worker, reply_queue, params, watcher_thread, context)

    if CONAN_MAJOR_VERSION == 1:
        assert "Unzipping" in caplog.text
    assert f"Configuration installed from {conan_config_zip}" in caplog.text
    assert replies
    assert isinstance(replies[0], Success)
    if CONAN_MAJOR_VERSION == 1:
        assert replies[0].payload is None  # TODO: why?
    else:
        assert replies[0].payload


def test_conan_config_install_from_git(
    multiprocess_reply_queue_fixture: MultiprocessReplyQueueFixture,
    run_worker: RunWorkerFixture,
    conan_local_cache: typing.Dict[str, str],
    conan_config_git_repo: pathlib.Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test: running conan config install with a Git repo."""
    caplog.set_level(logging.INFO)
    worker = workers_api.configinstall.invoke
    params = CommandParameters("install_config", worker)
    params.added_environment = conan_local_cache
    params.named_arguments["pathOrUrl"] = os.fspath(conan_config_git_repo)
    reply_queue, replies, watcher_thread, context = multiprocess_reply_queue_fixture()
    run_worker(worker, reply_queue, params, watcher_thread, context)

    if CONAN_MAJOR_VERSION == 1:
        assert "Processing" in caplog.text
    assert f"Configuration installed from {conan_config_git_repo}" in caplog.text
    assert replies
    assert isinstance(replies[0], Success)
    if CONAN_MAJOR_VERSION == 1:
        assert replies[0].payload is None  # TODO: why?
    else:
        assert replies[0].payload


def test_conan_config_install_with_git_branch(
    multiprocess_reply_queue_fixture: MultiprocessReplyQueueFixture,
    run_worker: RunWorkerFixture,
    conan_local_cache: typing.Dict[str, str],
    conan_config_git_repo: pathlib.Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test: running conan config install specifying a Git branch."""
    caplog.set_level(logging.INFO)

    git_branch_name = "main"

    worker = workers_api.configinstall.invoke
    params = CommandParameters("install_config", worker)
    params.added_environment = conan_local_cache
    params.named_arguments["pathOrUrl"] = os.fspath(conan_config_git_repo)
    params.named_arguments["gitBranch"] = git_branch_name
    reply_queue, replies, watcher_thread, context = multiprocess_reply_queue_fixture()
    run_worker(worker, reply_queue, params, watcher_thread, context)

    if CONAN_MAJOR_VERSION == 1:
        assert "Processing" in caplog.text
    assert f"Configuration installed from {conan_config_git_repo}" in caplog.text
    assert f"with arguments -b {git_branch_name}" in caplog.text
    assert replies
    assert isinstance(replies[0], Success)
    if CONAN_MAJOR_VERSION == 1:
        assert replies[0].payload is None  # TODO: why?
    else:
        assert replies[0].payload


def test_conan_config_install_with_missing_git_branch(
    multiprocess_reply_queue_fixture: MultiprocessReplyQueueFixture,
    run_worker: RunWorkerFixture,
    conan_local_cache: typing.Dict[str, str],
    conan_config_git_repo: pathlib.Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """
    Test: running conan config install specifying a Git branch that doesn't exist.

    Surprisingly Conan does not error on this.
    """
    caplog.set_level(logging.INFO)

    git_branch_name = "does_not_exist"

    worker = workers_api.configinstall.invoke
    params = CommandParameters("install_config", worker)
    params.added_environment = conan_local_cache
    params.named_arguments["pathOrUrl"] = os.fspath(conan_config_git_repo)
    params.named_arguments["gitBranch"] = git_branch_name
    reply_queue, replies, watcher_thread, context = multiprocess_reply_queue_fixture()
    run_worker(worker, reply_queue, params, watcher_thread, context)

    if CONAN_MAJOR_VERSION == 1:
        assert "Processing" in caplog.text
    assert f"Configuration installed from {conan_config_git_repo}" in caplog.text
    assert f"with arguments -b {git_branch_name}" in caplog.text
    assert replies
    assert isinstance(replies[0], Success)
    if CONAN_MAJOR_VERSION == 1:
        assert replies[0].payload is None  # TODO: why?
    else:
        assert replies[0].payload


def test_conan_config_install_from_source_folder(
    multiprocess_reply_queue_fixture: MultiprocessReplyQueueFixture,
    run_worker: RunWorkerFixture,
    conan_local_cache: typing.Dict[str, str],
    conan_config_zip: pathlib.Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """
    Test: running conan config install with a source folder in a zip file.

    Again surprisingly Conan does not error if the source folder does not exist.
    """
    caplog.set_level(logging.INFO)

    source_folder = "srcSubdir"

    worker = workers_api.configinstall.invoke
    params = CommandParameters("install_config", worker)
    params.added_environment = conan_local_cache
    params.named_arguments["pathOrUrl"] = os.fspath(conan_config_zip)
    params.named_arguments["sourceFolder"] = source_folder
    reply_queue, replies, watcher_thread, context = multiprocess_reply_queue_fixture()
    run_worker(worker, reply_queue, params, watcher_thread, context)

    if CONAN_MAJOR_VERSION == 1:
        assert "Unzipping" in caplog.text
    assert f"Configuration installed from {conan_config_zip}" in caplog.text
    assert f"from source folder {source_folder}" in caplog.text
    assert replies
    assert isinstance(replies[0], Success)
    if CONAN_MAJOR_VERSION == 1:
        assert replies[0].payload is None  # TODO: why?
    else:
        assert replies[0].payload


def test_conan_config_install_to_target_folder(
    multiprocess_reply_queue_fixture: MultiprocessReplyQueueFixture,
    run_worker: RunWorkerFixture,
    conan_local_cache: typing.Dict[str, str],
    conan_config_zip: pathlib.Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test: running conan config install to a target folder from a zip file."""
    caplog.set_level(logging.INFO)

    target_folder = "destSubdir"

    worker = workers_api.configinstall.invoke
    params = CommandParameters("install_config", worker)
    params.added_environment = conan_local_cache
    params.named_arguments["pathOrUrl"] = os.fspath(conan_config_zip)
    params.named_arguments["targetFolder"] = target_folder
    reply_queue, replies, watcher_thread, context = multiprocess_reply_queue_fixture()
    run_worker(worker, reply_queue, params, watcher_thread, context)

    if CONAN_MAJOR_VERSION == 1:
        assert "Unzipping" in caplog.text
    assert f"Configuration installed from {conan_config_zip}" in caplog.text
    assert f"to target folder {target_folder}" in caplog.text
    assert replies
    assert isinstance(replies[0], Success)
    if CONAN_MAJOR_VERSION == 1:
        assert replies[0].payload is None  # TODO: why?
    else:
        assert replies[0].payload
