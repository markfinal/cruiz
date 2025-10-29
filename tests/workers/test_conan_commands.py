"""Test the Conan command functionality."""

import multiprocessing

import cruizlib.workers.api as workers_api
from cruizlib.interop.commandparameters import CommandParameters


def test_conan_install() -> None:
    """Test: running conan install."""
    context = multiprocessing.get_context("spawn")
    reply_queue = context.Queue()
    params = CommandParameters("install", workers_api.install.invoke)
    params.worker(reply_queue, params)
