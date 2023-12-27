#!/usr/bin/env python3

"""
Child process commands
"""

from __future__ import annotations

import multiprocessing
import os
import pathlib
import urllib.parse
import typing

from cruiz.interop.commandparameters import CommandParameters
from cruiz.interop.pod import ConanRemote, ConanHook
from cruiz.interop.message import Message, Success, Failure

from . import worker


# pylint: disable=protected-access, import-outside-toplevel


# copied from distutils.url.strtobool and modified
def _strtobool(val: str) -> bool:
    """Convert a string representation of truth to true (1) or false (0).

    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return True
    if val in ("n", "no", "f", "false", "off", "0"):
        return False
    raise ValueError("invalid truth value %r" % (val,))


def _remotes_list(api: typing.Any) -> typing.List[ConanRemote]:
    result = api.remote_list()
    try:
        # conan 1.19+
        result2 = [
            ConanRemote(remote.name, remote.url, not remote.disabled)
            for remote in result
        ]
    except AttributeError:
        result2 = [ConanRemote(remote.name, remote.url, True) for remote in result]
    return result2


def _remotes_sync(api: typing.Any, remotes: typing.List[str]) -> None:
    for remote in _remotes_list(api):
        api.remote_remove(remote.name)
    for remote_str in remotes:
        remote = ConanRemote.from_string(remote_str)
        api.remote_add(remote.name, remote.url)
        api.remote_set_disabled_state(remote.name, not remote.enabled)


def _profiles_dir(api: typing.Any) -> pathlib.Path:
    # pylint: disable=pointless-statement
    try:
        # Conan 1.18+
        profile_dir = pathlib.Path(api.app.cache.profiles_path)
        if not profile_dir.is_dir():
            # this creates the default profile
            api.app.cache.default_profile
    except AttributeError:
        profile_dir = pathlib.Path(api._cache.profiles_path)
        if not profile_dir.is_dir():
            # this creates the default profile
            api._cache.default_profile
    return profile_dir


def _default_profile_path(api: typing.Any) -> str:
    try:
        # Conan 1.18+
        api.create_app()
        default_profile_path = api.app.cache.default_profile_path
    except AttributeError:
        api.invalidate_caches()
        default_profile_path = api._cache.default_profile_path
    return default_profile_path


def _profile_meta(
    api: typing.Any, profile: str
) -> typing.Dict[str, typing.Dict[str, typing.Any]]:
    result = api.read_profile(profile)
    details: typing.Dict[str, typing.Dict[str, typing.Any]] = {"settings": {}}
    for key, value in result.settings.items():
        details["settings"][key] = value
    return details


def _conan_version() -> str:
    import conans

    return conans.__version__


def _get_package_layout(
    api: typing.Any, reference: str, short_paths: bool
) -> typing.Tuple[typing.Any, typing.Any]:
    from conans.model.ref import ConanFileReference

    file_ref = ConanFileReference.loads(reference)
    try:
        # Conan 1.18+
        layout = api.app.cache.package_layout(file_ref, short_paths=short_paths)
    except AttributeError:
        layout = api._cache.package_layout(file_ref, short_paths=short_paths)
    return layout, file_ref


def _package_dir(
    api: typing.Any,
    reference: str,
    package_id: str,
    package_revision: str,
    short_paths: bool,
) -> pathlib.Path:
    from conans.model.ref import PackageReference

    layout, file_ref = _get_package_layout(api, reference, short_paths)
    pref = PackageReference(file_ref, package_id, package_revision)
    package_dir = layout.package(pref)
    return pathlib.Path(package_dir)


def _package_export_dir(api: typing.Any, reference: str, short_paths: bool) -> str:
    layout, _ = _get_package_layout(api, reference, short_paths)
    package_export_dir = layout.export()
    return package_export_dir


def _package_export_sources_dir(
    api: typing.Any, reference: str, short_paths: bool
) -> str:
    layout, _ = _get_package_layout(api, reference, short_paths)
    package_export_sources_dir = layout.export_sources()
    return package_export_sources_dir


def _editable_list(api: typing.Any) -> typing.List[str]:
    result = api.editable_list()
    return result


def _editable_add(api: typing.Any, ref: str, path: str) -> typing.Any:
    result = api.editable_add(
        path,
        ref,
        None,  # standard layout - use recipe dir to write package to
        None,  # cwd, fine to be None as the absolute path to the recipe is provided
    )
    return result


def _editable_remove(api: typing.Any, ref: str) -> typing.Any:
    result = api.editable_remove(ref)
    return result


def _inspect_recipe(api: typing.Any, recipe_path: str) -> typing.Dict[str, typing.Any]:
    result = api.inspect(recipe_path, None)  # get all attributes
    return result


def _hook_path(api: typing.Any) -> str:
    try:
        # conan 1.18+
        result = api.app.cache.hooks_path
    except AttributeError:
        result = api._cache.hooks_path
    return result


def _enabled_hooks(api: typing.Any) -> bool:
    try:
        # conan 1.18+
        result = api.app.cache.config.hooks
    except AttributeError:
        result = api._cache.config.hooks
    return result


def _available_hooks(api: typing.Any) -> typing.List[pathlib.Path]:
    try:
        # conan 1.18+
        hooks_dir = pathlib.Path(api.app.cache.hooks_path)
    except AttributeError:
        hooks_dir = pathlib.Path(api._cache.hooks_path)
    if not hooks_dir or not hooks_dir.is_dir():
        return []
    hook_files: typing.List[pathlib.Path] = []
    for root, dirs, files in os.walk(hooks_dir):
        if ".git" in dirs:
            # ignore .git folders
            dirs.remove(".git")
        for file in files:
            if file.endswith(".py"):
                full_path = pathlib.Path(root) / file
                stored_path = full_path.relative_to(hooks_dir)
                hook_files.append(stored_path)
    return hook_files


def _hooks_get(api: typing.Any) -> typing.List[ConanHook]:
    try:
        # conan 1.18+
        hooks_dir = pathlib.Path(api.app.cache.hooks_path)
        enabled_hooks = api.app.cache.config.hooks
    except AttributeError:
        hooks_dir = pathlib.Path(api._cache.hooks_path)
        enabled_hooks = api._cache.config.hooks
    if not hooks_dir or not hooks_dir.is_dir():
        return []
    hook_files: typing.List[ConanHook] = []
    for root, dirs, files in os.walk(hooks_dir):
        if ".git" in dirs:
            # ignore .git folders
            dirs.remove(".git")
        for file in files:
            if file.endswith(".py"):
                full_path = pathlib.Path(root) / file
                stored_path = full_path.relative_to(hooks_dir)
                hook_enabled = (
                    file in enabled_hooks or pathlib.Path(file).stem in enabled_hooks
                )
                hook_files.append(ConanHook(stored_path, hook_enabled))
    return hook_files


def _hooks_sync(api: typing.Any, hook_changes: typing.List[str]) -> None:
    for change in hook_changes:
        hook = ConanHook.from_string(change)
        hook_config = f"hooks.{hook.path}"
        if hook.enabled:
            _set_config(api, hook_config, None)
        else:
            if _has_config_option(api, "hooks", os.fspath(hook.path)):
                _rm_config(api, hook_config)
            else:
                no_ext_path = hook.path.stem
                hook_config = f"hooks.{no_ext_path}"
                assert _has_config_option(api, "hooks", no_ext_path)
                _rm_config(api, hook_config)


def _enable_hook(api: typing.Any, hook: str, hook_enabled: bool) -> None:
    hook = f"hooks.{hook}"
    if hook_enabled:
        _set_config(api, hook, None)
    else:
        _rm_config(api, hook)


def _get_conandata(api: typing.Any, recipe_path: str) -> typing.Dict[str, typing.Any]:
    try:
        # conan 1.18+
        result = api.app.loader._load_data(recipe_path)
    except AttributeError:
        result = api._cache.loader._load_data(recipe_path)
    return result


def _get_config(api: typing.Any, key: str) -> typing.Optional[str]:
    # pylint: disable=broad-except
    try:
        try:
            # conan 1.18+
            result = api.app.cache.config.get_item(key)
        except AttributeError:
            result = api._cache.config.get_item(key)
        return result
    except Exception:
        return None


def _set_config(api: typing.Any, key: str, value: typing.Optional[str]) -> None:
    try:
        # conan 1.18+
        api.app.cache.config.set_item(key, value)
    except AttributeError:
        api._cache.config.set_item(key, value)


def _rm_config(api: typing.Any, key: str) -> None:
    try:
        # conan 1.18+
        api.app.cache.config.rm_item(key)
    except AttributeError:
        api._cache.config.rm_item(key)


def _has_config_option(api: typing.Any, key: str, value: str) -> bool:
    try:
        # conan 1.18+
        return api.app.cache.config.has_option(key, value)
    except AttributeError:
        return api._cache.config.has_option(key, value)


def _get_config_envvars(api: typing.Any) -> typing.List[str]:
    try:
        # conan 1.18+
        return list(api.app.cache.config.env_vars.keys())
    except AttributeError:
        return list(api._cache.config.env_vars.keys())


def _create_default_profile(api: typing.Any) -> None:
    try:
        # Conan 1.18+
        api.create_app()
        api.app.cache.reset_default_profile()
    except AttributeError:
        api.invalidate_caches()
        api.create_profile("default", detect=True, force=True)


# pylint: disable=too-many-statements
def invoke(
    request_queue: multiprocessing.JoinableQueue[str],
    reply_queue: multiprocessing.Queue[Message],
    params: CommandParameters,
) -> None:
    # pylint: disable=too-many-branches
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
                if request == "remotes_list":
                    result = _remotes_list(api)
                elif request == "remotes_sync":
                    _remotes_sync(api, request_params["remotes"])
                    result = None
                elif request == "profiles_dir":
                    result = _profiles_dir(api)  # type: ignore[assignment]
                elif request == "default_profile_path":
                    result = _default_profile_path(api)  # type: ignore[assignment]
                elif request == "profile_meta":
                    result = _profile_meta(
                        api, request_params["name"][0]
                    )  # type: ignore[assignment]
                elif request == "version":
                    result = _conan_version()  # type: ignore[assignment]
                elif request == "package_dir":
                    result = _package_dir(  # type: ignore[assignment]
                        api,
                        request_params["ref"][0],
                        request_params["package_id"][0],
                        request_params["revision"][0],
                        _strtobool(request_params["short_paths"][0]),
                    )
                elif request == "package_export_dir":
                    result = _package_export_dir(  # type: ignore[assignment]
                        api,
                        request_params["ref"][0],
                        _strtobool(request_params["short_paths"][0]),
                    )
                elif request == "package_export_sources_dir":
                    result = _package_export_sources_dir(  # type: ignore[assignment]
                        api,
                        request_params["ref"][0],
                        _strtobool(request_params["short_paths"][0]),
                    )
                elif request == "editable_list":
                    result = _editable_list(api)  # type: ignore[assignment]
                elif request == "editable_add":
                    result = _editable_add(
                        api, request_params["ref"][0], request_params["path"][0]
                    )
                elif request == "editable_remove":
                    result = _editable_remove(api, request_params["ref"][0])
                elif request == "inspect_recipe":
                    result = _inspect_recipe(
                        api, request_params["path"][0]
                    )  # type: ignore[assignment]
                elif request == "hook_path":
                    result = _hook_path(api)  # type: ignore[assignment]
                elif request == "enabled_hooks":
                    result = _enabled_hooks(api)  # type: ignore[assignment]
                elif request == "available_hooks":
                    result = _available_hooks(api)  # type: ignore[assignment]
                elif request == "get_hooks":
                    result = _hooks_get(api)  # type: ignore[assignment]
                elif request == "hooks_sync":
                    _hooks_sync(api, request_params["hooks"])
                    result = None
                elif request == "enable_hook":
                    _enable_hook(
                        api,
                        request_params["hook"][0],
                        _strtobool(request_params["hook_enabled"][0]),
                    )
                    result = None
                elif request == "get_cmake_generator":
                    result = _get_config(
                        api, "general.cmake_generator"
                    )  # type: ignore[assignment]
                elif request == "get_conandata":
                    result = _get_conandata(
                        api, request_params["path"][0]
                    )  # type: ignore[assignment]
                elif request == "get_config":
                    result = _get_config(
                        api, request_params["config"][0]
                    )  # type: ignore[assignment]
                elif request == "set_config":
                    _set_config(
                        api,
                        request_params["config"][0],
                        request_params["value"][0],
                    )
                    result = None
                elif request == "get_config_envvars":
                    result = _get_config_envvars(api)  # type: ignore[assignment]
                elif request == "create_default_profile":
                    _create_default_profile(api)
                    result = None
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
