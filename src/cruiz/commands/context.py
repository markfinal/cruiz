#!/usr/bin/env python3

"""A context object wrapping the Conan API."""

from __future__ import annotations

import logging
import pathlib
import typing
from contextlib import contextmanager

from PySide6 import QtCore, QtWidgets

from attr.converters import to_bool

from cruiz.exceptions import RecipeInspectionError
from cruiz.recipe.logs.command import CommandListWidgetItem, RecipeCommandHistoryWidget
from cruiz.settings.managers.namedlocalcache import NamedLocalCacheSettingsReader

import cruizlib.workers.api as workers_api
from cruizlib.constants import DEFAULT_CACHE_NAME
from cruizlib.interop.commandparameters import CommandParameters
from cruizlib.workers.utils.text2html import text_to_html

from .conanenv import get_conan_env
from .conaninvocation import ConanInvocation
from .metarequestconaninvocation import MetaRequestConanInvocation

if typing.TYPE_CHECKING:
    from cruiz.interop.packagebinaryparameters import PackageBinaryParameters
    from cruiz.interop.packageidparameters import PackageIdParameters
    from cruiz.interop.packagerevisionsparameters import PackageRevisionsParameters
    from cruiz.interop.reciperevisionsparameters import RecipeRevisionsParameters
    from cruiz.interop.searchrecipesparameters import SearchRecipesParameters

    from cruizlib.interop.packagenode import PackageNode
    from cruizlib.interop.pod import ConanHook, ConanRemote

    from .conanconf import ConanConfigBoolean
    from .logdetails import LogDetails

logger = logging.getLogger(__name__)


class ConanContext(QtCore.QObject):
    """
    Context for invoking Conan instances.

    Some are for long running commands, with a background thread to process information.
    Others are for just quering meta data.
    """

    completed = QtCore.Signal(object, Exception)
    cancelled = QtCore.Signal()

    def __del__(self) -> None:
        """Log when a ConanContext is deleted."""
        logger.debug("-=%d", id(self))

    def __init__(
        self,
        cache_name: str,
        log_details: LogDetails,
    ) -> None:
        """Initialise a ConanContext."""
        logger.debug("+=%d", id(self))
        super().__init__(None)
        self.command_history_widget: typing.Optional[RecipeCommandHistoryWidget] = None
        self._log_details = log_details
        self._invocations: typing.List[ConanInvocation] = []
        self._configure_to_local_cache(cache_name)

    def close(self) -> None:
        """Close the context and any resources associated with it."""
        try:
            assert not self.is_busy
            self._meta_invocation.close()
            self._meta_invocation.deleteLater()
            del self._meta_invocation
        except AttributeError:
            # don't double close this
            pass

    def change_cache(self, cache_name: str, force: bool = False) -> None:
        """Change the local cache used by this context."""
        # don't even try to check for a name no-op if the cache has already been closed
        if hasattr(self, "_meta_invocation"):
            if cache_name == self.cache_name and not force:
                return
            assert not self.is_busy
            self.close()
        self._configure_to_local_cache(cache_name)

    def _configure_to_local_cache(self, cache_name: str) -> None:
        self.cache_name = cache_name
        self._meta_invocation = MetaRequestConanInvocation(
            self,
            cache_name,
            self._log_details,
        )

    def _start_invocation(
        self,
        parameters: typing.Union[
            CommandParameters,
            SearchRecipesParameters,
            RecipeRevisionsParameters,
            PackageIdParameters,
            PackageRevisionsParameters,
            PackageBinaryParameters,
        ],
        command_toolbar: typing.Optional[QtWidgets.QWidget],
        continuation: typing.Optional[typing.Callable[[typing.Any, typing.Any], None]],
        enable_history: bool = True,
    ) -> None:
        added_environment, removed_environment = get_conan_env(self.cache_name)
        parameters.added_environment.update(added_environment)
        parameters.removed_environment.extend(removed_environment)
        instance = ConanInvocation()
        instance.completed.connect(self._completed_invocation)
        instance.finished.connect(self._finished_invocation)
        if command_toolbar:
            instance.finished.connect(command_toolbar.command_ended)  # type: ignore[attr-defined] # noqa: E501
        instance.invoke(parameters, self._log_details, continuation)
        self._invocations.append(instance)
        if self.command_history_widget is not None and enable_history:
            # TODO: prefer adding to a model?
            assert isinstance(parameters, CommandParameters)
            item = CommandListWidgetItem(parameters)
            # don't duplicate the most recent command
            history_count = self.command_history_widget.count()
            if not history_count or (
                item.text()
                != self.command_history_widget.item(history_count - 1).text()
            ):
                self.command_history_widget.addItem(item)

    def _completed_invocation(self, success: typing.Any, exception: typing.Any) -> None:
        # pylint: disable=unused-argument
        logger.debug("COMPLETED invocation (%d)", id(self.sender()))
        sender_invocation = self.sender()
        assert isinstance(sender_invocation, ConanInvocation)
        sender_invocation.close()

    def _finished_invocation(self) -> None:
        # can only free the reference to the ConanInvocation once the message processing
        # thread has been destroyed
        instance = self.sender()
        logger.debug("FINISHED invocation (%d)", id(instance))
        instance.deleteLater()
        assert isinstance(instance, ConanInvocation)
        self._invocations.remove(instance)

    def conancommand(
        self,
        params: CommandParameters,
        command_toolbar: typing.Optional[QtWidgets.QWidget],
        continuation: typing.Optional[
            typing.Callable[[typing.Any, typing.Any], None]
        ] = None,
    ) -> None:
        """
        Run a conan command.

        Use parameters as provided, and a continuation if further processing is needed.
        """
        self._start_invocation(params, command_toolbar, continuation)

    def cmakebuildcommand(
        self,
        params: CommandParameters,
        command_toolbar: typing.Optional[QtWidgets.QWidget],
        continuation: typing.Optional[
            typing.Callable[[typing.Any, typing.Any], None]
        ] = None,
    ) -> None:
        """Invoke the CMake build tool on the build folder of the recipe."""
        self._start_invocation(
            params,
            command_toolbar,
            continuation,
            enable_history=False,
        )

    """
    def _make_symbolic_link(self, source: pathlib.Path, link: pathlib.Path) -> None:
        if link.exists():
            assert link.is_symlink()
            return
        if not link.parent.exists():
            os.makedirs(link.parent)
        # on Windows, os.symlink requires elevated privileges, or in developer mode
        # from Py3.8 although I cannot get the developer mode to work
        # additionally though, on Windows, I can't then open the symbolic link file
        # from Explorer even though a cmd dir command does show what its linked to
        os.symlink(source, link)
    """

    @staticmethod
    def _make_hard_link(source: pathlib.Path, link: pathlib.Path) -> None:
        if link.exists():
            if source.samefile(link):
                return
            # the inode may have changed, so just remove the old link, and recreate
            link.unlink()
        link.parent.mkdir(parents=True, exist_ok=True)
        link.hardlink_to(source)

    def editable_add(
        self,
        ref: str,
        recipe_path: pathlib.Path,
        config_subdir: str,
        continuation: typing.Optional[typing.Callable[[typing.Any, typing.Any], None]],
    ) -> None:
        """Run 'conan editable add'."""
        # this path has to match that in BaseCommand._get_paths
        package_dir = recipe_path.parent / "_edit_" / config_subdir / "package"
        target_symlink = package_dir / recipe_path.name
        # since the path changes with profile, always try to create a link
        # if it doesn't already exist
        ConanContext._make_hard_link(recipe_path, target_symlink)

        result, exception = self._meta_invocation.request_data(
            "editable_add", {"ref": ref, "path": str(target_symlink)}
        )
        if exception:
            raise Exception("Editable add failed") from exception
        if continuation:
            continuation(result, exception)

    def editable_remove(
        self,
        ref: str,
        continuation: typing.Optional[typing.Callable[[typing.Any, typing.Any], None]],
    ) -> None:
        """Run 'conan editable remove'."""
        result, exception = self._meta_invocation.request_data(
            "editable_remove", {"ref": ref}
        )
        if exception:
            raise Exception("Editable remove failed") from exception
        if continuation:
            continuation(result, exception)

    def remove_all_packages(
        self,
        continuation: typing.Optional[typing.Callable[[typing.Any, typing.Any], None]],
    ) -> None:
        """Run 'conan remove [-f] *'."""
        params = CommandParameters(
            "removeallpackages", workers_api.removeallpackages.invoke
        )
        params.force = True
        self._start_invocation(params, None, continuation)

    def remove_local_cache_locks(
        self,
        continuation: typing.Optional[typing.Callable[[typing.Any, typing.Any], None]],
    ) -> None:
        """Run 'conan remove --locks' to remove all lock files from the local cache."""
        params = CommandParameters("removelocks", workers_api.removelocks.invoke)
        self._start_invocation(params, None, continuation)

    def install_config(
        self,
        params: CommandParameters,
        continuation: typing.Optional[
            typing.Callable[[typing.Any, typing.Any], None]
        ] = None,
    ) -> None:
        """Run 'conan config install <URI> [--args -b branch] [-s source] [-t target]'."""  # noqa: E501
        self._start_invocation(params, None, continuation)

    def remotes_sync(self, remotes: typing.List[ConanRemote]) -> None:
        """Sync the remotes to the given list."""
        _, exception = self._meta_invocation.request_data(
            "remotes_sync", {"remotes": remotes}
        )
        if exception:
            raise Exception("Sync remotes failed") from exception

    def get_remotes_list(self) -> typing.List[ConanRemote]:
        """Equivalent to 'conan remote list'."""
        remotes_list, exception = self._meta_invocation.request_data("remotes_list")
        if exception:
            raise Exception("Get remote list failed") from exception
        assert isinstance(remotes_list, list)
        return remotes_list

    def get_profile_meta(
        self, profile_name: str
    ) -> typing.Dict[str, typing.Dict[str, str]]:
        """Get the meta information for a named profile."""
        result, exception = self._meta_invocation.request_data(
            "profile_meta", {"name": profile_name}
        )
        if exception:
            raise Exception("Get profile meta failed") from exception
        assert isinstance(result, dict)
        return result

    def get_package_details(
        self,
        params: typing.Union[
            SearchRecipesParameters,
            RecipeRevisionsParameters,
            PackageIdParameters,
            PackageRevisionsParameters,
            PackageBinaryParameters,
        ],
        continuation: typing.Optional[typing.Callable[[typing.Any, typing.Any], None]],
    ) -> None:
        """Perform one of the actions to get package details from a remote."""
        self._start_invocation(params, None, continuation)

    def get_package_directory(self, pkgdata: PackageNode) -> pathlib.Path:
        """Get the package directory for the specified package."""
        package_dir, exception = self._meta_invocation.request_data(
            "package_dir",
            {
                "ref": pkgdata.reference,
                "package_id": pkgdata.package_id,
                "revision": pkgdata.recipe_revision,
                "short_paths": pkgdata.short_paths,
            },
        )
        if exception:
            raise Exception("Get package directory failed") from exception
        assert isinstance(package_dir, pathlib.Path)
        return package_dir

    def cancel(self) -> None:
        """Cancel any current running worker thread."""
        if self._invocations:
            for invocation in self._invocations:
                invocation.cancel()
                invocation.close()
            self.cancelled.emit()

    def conan_version(self) -> str:
        """Get the Conan version."""
        version, exception = self._meta_invocation.request_data("version")
        if exception:
            raise Exception("Get Conan version failed") from exception
        assert isinstance(version, str)
        return version

    def profiles_dir(self) -> pathlib.Path:
        """Get the directory containing the profiles in the local cache."""
        profiles_dir, exception = self._meta_invocation.request_data("profiles_dir")
        if exception:
            raise Exception("Get profiles directory failed") from exception
        assert isinstance(profiles_dir, pathlib.Path)
        return pathlib.Path(profiles_dir)

    def all_profile_dirs(self) -> typing.List[pathlib.Path]:
        """Get a list of all profile directories inspected."""
        profile_dirs = [self.profiles_dir()]
        with NamedLocalCacheSettingsReader(self.cache_name) as settings:
            extra_profile_dirs = settings.extra_profile_directories.resolve()
        for _, dir_path in extra_profile_dirs.items():
            profile_dirs.append(pathlib.Path(dir_path))
        return profile_dirs

    def default_profile_path(self) -> str:
        """Get the default profile path from the Conan object."""
        default_path, exception = self._meta_invocation.request_data(
            "default_profile_path"
        )
        if exception:
            raise Exception("Get default profile path failed") from exception
        assert isinstance(default_path, str)
        return default_path

    def default_profile_filename(self) -> str:
        """Query Conan for the default profile filename."""
        return str(
            pathlib.Path(self.default_profile_path()).relative_to(self.profiles_dir())
        )

    def get_list_of_profiles(self) -> typing.List[typing.Tuple[pathlib.Path, str]]:
        """Return a list of all profiles in this context."""
        profile_paths: typing.List[typing.Tuple[pathlib.Path, str]] = []
        # TODO: Conan2 candidate: api.profiles.list() for the local-cache based profiles
        profiles_dir = QtCore.QDir(str(self.profiles_dir()))
        for profile in profiles_dir.entryList(filters=QtCore.QDir.Filter.Files):
            # local cache profiles are listed relative
            path = pathlib.Path(profiles_dir.filePath(profile))
            text = path.read_text(encoding="utf-8")
            profile_paths.append((pathlib.Path(path.name), text))
        # in Conan 2, there can be no profiles at this point
        with NamedLocalCacheSettingsReader(self.cache_name) as settings:
            extra_profile_dirs = settings.extra_profile_directories.resolve()
        for _, extra_profile_dir in extra_profile_dirs.items():
            profiles_dir = QtCore.QDir(extra_profile_dir)
            for profile in profiles_dir.entryList(filters=QtCore.QDir.Filter.Files):
                # extra profiles are listed absolute
                path = pathlib.Path(profiles_dir.filePath(profile))
                text = path.read_text(encoding="utf-8")
                profile_paths.append((path, text))
        return profile_paths

    def run_any_command(
        self,
        params: CommandParameters,
        continuation: typing.Callable[[typing.Any, typing.Any], None],
    ) -> None:
        """Run an arbitrary Conan command in the local cache."""
        self._start_invocation(params, None, continuation)

    # TODO: remove editables
    def get_editables_list(self) -> typing.Dict[str, str]:
        """Equivalent to 'conan editable list'."""
        editable_dict, exception = self._meta_invocation.request_data("editable_list")
        if exception:
            raise Exception("Get editables list failed") from exception
        assert isinstance(editable_dict, dict)
        return editable_dict

    def inspect_recipe(
        self, recipe_path: pathlib.Path, propagate_errors: bool = False
    ) -> typing.Dict[str, str]:
        """Equivalent to 'conan inspect'."""
        results, exception = self._meta_invocation.request_data(
            "inspect_recipe", {"path": recipe_path}
        )
        if exception:
            html = "<font color='red'>"
            html += text_to_html(str(exception))
            html += "</font>"
            self._log_details.stderr(
                f"Exception raised from running command:<br>" f"{html}<br>"
            )
            if propagate_errors:
                raise RecipeInspectionError()
            return {}
        assert isinstance(results, dict)
        return results

    def get_hooks_list(self) -> typing.List[ConanHook]:
        """
        No equivalent on the command line.

        But lists all hooks in the config and their enabled states.
        """
        hooks_list, exception = self._meta_invocation.request_data("get_hooks")
        if exception:
            raise Exception("Get hooks list failed") from exception
        assert isinstance(hooks_list, list)
        return hooks_list

    def hooks_sync(self, hook_changes: typing.List[ConanHook]) -> None:
        """Equivalent to either conan config set <hook> or conan config rm <hook>."""
        _, exception = self._meta_invocation.request_data(
            "hooks_sync", {"hooks": hook_changes}
        )
        if exception:
            raise Exception("Syncing hooks failed") from exception

    def enable_hook(self, hook: str, enabled: bool) -> None:
        """Equivalent to either conan config set <hook> or conan config rm <hook>."""
        _, exception = self._meta_invocation.request_data(
            "enable_hook", {"hook": hook, "hook_enabled": enabled}
        )
        if exception:
            raise Exception("Enable/disable hook failed") from exception

    def get_cmake_generator(self) -> str:
        """Equivalent to conan config get general.cmake_generator."""
        generator, exception = self._meta_invocation.request_data(
            "get_cmake_generator", {}
        )
        if exception:
            raise Exception("Failed to get CMake generator") from exception
        return generator

    def get_conandata(
        self, recipe_path: pathlib.Path
    ) -> typing.Dict[str, typing.Dict[str, str]]:
        """Fetch the YAML dictionary of the conandata.yml beside the recipe."""
        conandata, exception = self._meta_invocation.request_data(
            "get_conandata", {"path": recipe_path}
        )
        if exception:
            raise ValueError(
                "Failed to get conandata YAML dict for recipe"
            ) from exception
        return conandata

    def get_boolean_config(
        self, config: ConanConfigBoolean, default_value: bool
    ) -> bool:
        """
        Equivalent to conan config get.

        Use the specified config key.
        If the specified config key is not in the configuration, return the default
        value.
        """
        config_value, exception = self._meta_invocation.request_data(
            "get_config", {"config": config.value}
        )
        if exception:
            raise Exception(
                f"Failed to get local cache config for '{config.value}'"
            ) from exception
        if config_value is not None:
            assert isinstance(config_value, str)
            config_value = to_bool(config_value)
        return config_value or default_value

    def set_boolean_config(self, config: ConanConfigBoolean, value: bool) -> None:
        """Equivalent to conan config set, with the specified config key and value."""
        _, exception = self._meta_invocation.request_data(
            "set_config", {"config": config.value, "value": str(value)}
        )
        if exception:
            raise Exception(
                f"Failed to set local cache config for '{config.value}'"
            ) from exception

    @property
    def is_default(self) -> bool:
        """Does this context refer to the 'default' local cache?."""
        return self.cache_name == DEFAULT_CACHE_NAME

    def get_conan_config_environment_variables(self) -> typing.List[str]:
        """
        Get a list of all Conan environment variables names.

        This doesn't get all of them, but at least some.
        """
        envvars, exception = self._meta_invocation.request_data("get_config_envvars")
        if exception:
            raise Exception(
                "Failed to get Conan config environment variables"
            ) from exception
        return envvars

    @property
    def is_busy(self) -> bool:
        """
        Is the context busy running any Conan commands?.

        Explicitly or via its meta commands
        """
        return bool(self._invocations) or self._meta_invocation.active

    def create_default_profile(self) -> None:
        """
        Create the default profile in the local cache by detecting the environment.

        This will overwrite any existing default profile.
        """
        _, exception = self._meta_invocation.request_data("create_default_profile")
        if exception:
            raise Exception(
                "Creating the default profile for the local cache failed"
            ) from exception


@contextmanager
def managed_conan_context(
    cache_name: str, log_details: LogDetails
) -> typing.Generator[ConanContext, None, None]:
    """
    Context manager for the ConanContext.

    For uses where all API calls on the ConanContext are guaranteed to be synchronous.
    """
    context = ConanContext(cache_name, log_details)
    try:
        yield context
    finally:
        context.close()
