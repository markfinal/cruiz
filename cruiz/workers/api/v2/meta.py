#!/usr/bin/env python3

"""
Meta commands are short lived queries that do not warrant having their own
process spun up to resolve.

One long-lived meta process runs continually to service these.
"""

from __future__ import annotations

import multiprocessing
import pathlib
import urllib.parse
import typing

from cruiz.interop.commandparameters import CommandParameters
from cruiz.interop.message import Message, Failure, Success
from cruiz.interop.pod import ConanRemote

from . import worker


def _interop_remote_list(api: typing.Any) -> typing.List[ConanRemote]:
    interop_list: typing.List[ConanRemote] = []
    for remote in api.remotes.list(only_enabled=False):
        interop_list.append(ConanRemote(remote.name, remote.url, not remote.disabled))
    return interop_list


def _interop_get_config(api: typing.Any, key: str) -> typing.Optional[str]:
    return api.config.get(key)


def _interop_profiles_dir(api: typing.Any) -> pathlib.Path:
    from conan.internal.conan_app import ConanApp

    app = ConanApp(api.cache_folder)
    return pathlib.Path(app.cache.profiles_path)


def invoke(
    request_queue: multiprocessing.JoinableQueue[str],
    reply_queue: multiprocessing.Queue[Message],
    params: CommandParameters,
) -> None:
    """
    Run continuous loop, waiting on requests from the main process
    """
    with worker.ConanWorker(reply_queue, params) as api:
        while True:
            try:
                request = request_queue.get()
                if request == "end":
                    request_queue.task_done()
                    break
                if "?" in request:
                    split = request.split("?")
                    request = split[0]
                    request_params = urllib.parse.parse_qs(split[1])

                result: typing.Any = None
                if request == "remotes_list":
                    result = _interop_remote_list(api)
                elif request == "get_config":
                    result = _interop_get_config(api, request_params["config"][0])
                elif request == "profiles_dir":
                    result = _interop_profiles_dir(api)
                else:
                    raise RuntimeError(
                        f"Unhandled request '{request}', '{request_params}'"
                    )
                reply_queue.put(Success(result))
                request_queue.task_done()
                # ensure that the result doesn't accidentally appear in
                # subsequent loop iterations
                del result
            # pylint: disable=broad-except
            except Exception as exception:
                reply_queue.put(Failure(Exception(str(exception))))
                request_queue.task_done()
    request_queue.join()
    request_queue.close()
    request_queue.join_thread()
