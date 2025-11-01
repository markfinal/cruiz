"""Tests for running commands through subprocess."""

from __future__ import annotations

import os
import typing

from cruizlib.runcommands import (
    get_popen_for_capture,
    run,
    run_get_combined_output,
    run_get_output,
)

if typing.TYPE_CHECKING:
    import pytest_subprocess


EOL = "\r\n" if os.name == "nt" else "\n"


def test_run(fake_process: pytest_subprocess.FakeProcess) -> None:
    """Exercise the run function."""
    fake_process.register(["git", "branch"], stdout=["* fake_branch", "  main"])
    process = run(["git", "branch"], capture_output=True)
    assert not process.returncode
    assert process.stdout == f"* fake_branch{EOL}  main{EOL}"


def test_run_for_output(fake_process: pytest_subprocess.FakeProcess) -> None:
    """Exercise the run_get_output function."""
    fake_process.register(["git", "branch"], stdout=["* fake_branch", "  main"])
    output = run_get_output(["git", "branch"])
    assert output == f"* fake_branch{EOL}  main{EOL}"


def test_run_for_combined_output(fake_process: pytest_subprocess.FakeProcess) -> None:
    """Exercise the run_get_combined_output function."""
    fake_process.register(
        ["git", "branch"],
        stdout=["* fake_branch", "  main"],
        stderr=["There is no error"],
    )
    output = run_get_combined_output(["git", "branch"])
    assert output == f"* fake_branch{EOL}  main{EOL}There is no error{EOL}"


def test_run_popen(fake_process: pytest_subprocess.FakeProcess) -> None:
    """Exercise the get_popen_for_capture function."""
    fake_process.register(["git", "branch"], stdout=["* fake_branch", "  main"])
    with get_popen_for_capture(["git", "branch"]) as process:
        assert process.stdout
        assert process.stdout.readline() == f"* fake_branch{EOL}"
        assert process.stdout.readline() == f"  main{EOL}"
