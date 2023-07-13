#!/usr/bin/env python3

"""
Meta commands are short lived queries that do not warrant having their own
process spun up to resolve.

One long-lived meta process runs continually to service these.
"""

from __future__ import annotations

import multiprocessing
import os
import pathlib
import urllib.parse
import typing

from cruiz.interop.commandparameters import CommandParameters
from cruiz.interop.message import Message, Failure, Success
from cruiz.interop.pod import ConanRemote, ConanHook

from . import worker


def _interop_remote_list(api: typing.Any) -> typing.List[ConanRemote]:
    interop_list: typing.List[ConanRemote] = []
    for remote in api.remotes.list(only_enabled=False):
        interop_list.append(ConanRemote(remote.name, remote.url, not remote.disabled))
    return interop_list


def _interop_remotes_sync(api: typing.Any, remotes: typing.List[str]) -> None:
    from conans.client.cache.remote_registry import Remote

    for remote in _interop_remote_list(api):
        api.remotes.remove(remote.name)
    for remote_str in remotes:
        remote = ConanRemote.from_string(remote_str)
        conan_remote = Remote(remote.name, remote.url)
        api.remotes.add(conan_remote)
        if remote.enabled:
            api.remotes.enable(remote.name)
        else:
            api.remotes.disable(remote.name)


def _interop_get_config(api: typing.Any, key: str) -> typing.Optional[str]:
    return api.config.get(key)


def _interop_profiles_dir(api: typing.Any) -> pathlib.Path:
    from conan.internal.conan_app import ConanApp

    app = ConanApp(api.cache_folder)
    return pathlib.Path(app.cache.profiles_path)


def _interop_get_hooks(api: typing.Any) -> typing.List[ConanHook]:
    from conan.internal.conan_app import ConanApp

    app = ConanApp(api.cache_folder)

    hooks_dir = app.cache.hooks_path

    hook_files: typing.List[ConanHook] = []
    for root, dirs, files in os.walk(hooks_dir):
        if ".git" in dirs:
            # ignore .git folders
            dirs.remove(".git")
        for file in files:
            if file.endswith(".py"):
                full_path = pathlib.Path(root) / file
                stored_path = full_path.relative_to(hooks_dir)
                # in Conan 2, hooks are activated by having them in the folder
                hook_files.append(ConanHook(stored_path, enabled=True))

    return hook_files


def _interop_inspect_recipe(
    api: typing.Any, recipe_path: str
) -> typing.Dict[str, typing.Any]:
    conanfile = api.local.inspect(recipe_path, None, None)
    result = conanfile.serialize()
    return result


def _interop_create_default_profile(api: typing.Any) -> None:
    from conans.util.files import save

    profile_pathname = api.profiles.get_path("default", os.getcwd(), exists=False)
    save(profile_pathname, api.profiles.detect().dumps())


def _interop_get_conandata(
    api: typing.Any, recipe_path: str
) -> typing.Dict[str, typing.Any]:
    from conan.internal.conan_app import ConanApp

    app = ConanApp(api.cache_folder)
    return app.loader._load_data(recipe_path)


def _interop_get_config_envvars(api: typing.Any) -> typing.List[str]:
    # no variable present listing the all in Conan 2
    # so use https://docs.conan.io/2/reference/environment.html
    envvar_list = [
        "CONAN_HOME",
        "CONAN_DEFAULT_PROFILE",
        "CONAN_LOGIN_USERNAME",
        "CONAN_PASSWORD",
        "CONAN_COLOR_DARK",
    ]
    return envvar_list


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
                elif request == "remotes_sync":
                    _interop_remotes_sync(api, request_params["remotes"])
                    result = None
                elif request == "get_config":
                    result = _interop_get_config(api, request_params["config"][0])
                elif request == "profiles_dir":
                    result = _interop_profiles_dir(api)
                elif request == "get_hooks":
                    result = _interop_get_hooks(api)
                elif request == "inspect_recipe":
                    result = _interop_inspect_recipe(api, request_params["path"][0])
                elif request == "create_default_profile":
                    _interop_create_default_profile(api)
                    result = None
                elif request == "get_conandata":
                    result = _interop_get_conandata(api, request_params["path"][0])
                elif request == "get_config_envvars":
                    result = _interop_get_config_envvars(api)
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
