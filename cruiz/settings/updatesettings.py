#!/usr/bin/env python3

"""
Patching settings
"""

from __future__ import annotations

import pathlib
import shutil
import time
import typing

from qtpy import QtCore

from .managers.basesettings import BaseSettings


CURRENT_SETTINGS_VERSION = 9


class SettingsGroup:
    """
    Context manager for using groups in QSettings
    """

    def __init__(self, settings: QtCore.QSettings, group: str) -> None:
        self._settings = settings
        self._group_name = group

    def __enter__(self) -> None:
        self._settings.beginGroup(self._group_name)

    def __exit__(
        self, exc_type: typing.Any, value: typing.Any, exc_traceback: typing.Any
    ) -> None:
        self._settings.endGroup()


class SettingsReadArray:
    """
    Context manager for reading arrays in QSettings
    """

    def __init__(self, settings: QtCore.QSettings, array: str) -> None:
        self._settings = settings
        self._array_name = array
        self._array_size = 0

    # TODO: why isn't this just a public attribute?
    @property
    def size(self) -> int:
        """
        Property containing the size of the array found in the settings
        """
        return self._array_size

    def __enter__(self) -> SettingsReadArray:
        self._array_size = self._settings.beginReadArray(self._array_name)
        return self

    def __exit__(
        self, exc_type: typing.Any, value: typing.Any, exc_traceback: typing.Any
    ) -> None:
        self._settings.endArray()


class SettingsWriteArray:
    """
    Context manager for writing arrays in QSettings
    """

    def __init__(self, settings: QtCore.QSettings, array: str, size: int) -> None:
        self._settings = settings
        self._array_name = array
        self._array_size = size

    def __enter__(self) -> None:
        self._settings.beginWriteArray(self._array_name, self._array_size)

    def __exit__(
        self, exc_type: typing.Any, value: typing.Any, exc_traceback: typing.Any
    ) -> None:
        self._settings.endArray()


def _patch_settings_from_v8(settings: QtCore.QSettings) -> None:
    """
    Remove
      - DarkMode
    """
    settings.remove("DarkMode")


def _patch_settings_from_v7(settings: QtCore.QSettings) -> None:
    """
    Remove
      - NewLoadingBehaviour
      - UseCompactLook
    Rename
      - DefaultRenderDirectory to DefaultRecipeDirectory
    """
    settings.remove("NewLoadingBehaviour")
    settings.remove("UseCompactLook")
    old_defaultrecipedir = settings.value("DefaultRenderDirectory")
    settings.remove("DefaultRenderDirectory")
    if old_defaultrecipedir:
        settings.setValue("DefaultRecipeDirectory", old_defaultrecipedir)


def _patch_settings_from_v6(settings: QtCore.QSettings) -> None:
    """
    V2Mode and UseRevisions move from global settings to per-cache
    If either were true, this was global, so apply to all caches
    """
    old_v2mode = settings.value("Conan/V2Mode", False, type=bool)
    settings.remove("Conan/V2Mode")
    old_userevisions = settings.value("Conan/Revisions", False, type=bool)
    settings.remove("Conan/Revisions")
    if old_v2mode or old_userevisions:
        with SettingsReadArray(settings, "Conan/LocalCaches") as array:
            num_caches = array.size
        with SettingsWriteArray(settings, "Conan/LocalCaches", num_caches):
            for i in range(num_caches):
                settings.setArrayIndex(i)
                if old_v2mode:
                    settings.setValue("V2Mode", old_v2mode)
                if old_userevisions:
                    settings.setValue("Revisions", old_userevisions)


def _patch_settings_from_v5(settings: QtCore.QSettings) -> None:
    """
    Moves recent recipe paths from the recent recipe array to the recipe array.
    """
    recipes = []
    with SettingsReadArray(settings, "RecentRecipes") as array:
        for i in range(array.size):
            settings.setArrayIndex(i)
            recipes.append(
                (
                    settings.value("UUID"),
                    settings.value("Path"),
                )
            )
    settings.remove("RecentRecipes")
    with SettingsWriteArray(settings, "RecentRecipes", len(recipes)):
        for i, (uuid, _) in enumerate(recipes):
            settings.setArrayIndex(i)
            settings.setValue("UUID", uuid)
    for uuid, path in recipes:
        group = f"Recipe/{uuid}"
        with SettingsGroup(settings, group):
            settings.setValue("Path", path)


def _patch_settings_from_v4(settings: QtCore.QSettings) -> None:
    """
    This patch refactors any editables keys.
    "Name" is converted to "Reference", and reformats the value so it's back to being
    a Conan Reference (so matches that in the local cache's editables.json keys) rather
    than a file-system safe component.
    Also the "Path" key is renamed to "RecipePath".
    """
    uuids = []
    with SettingsReadArray(settings, "RecentRecipes") as array:
        for i in range(array.size):
            settings.setArrayIndex(i)
            uuids.append(settings.value("UUID"))
    for uuid in uuids:
        group = f"Recipe/{uuid}"
        with SettingsGroup(settings, group):
            editables: typing.List[typing.Dict[str, object]] = []
            with SettingsReadArray(settings, "Editables") as array:
                for i in range(array.size):
                    editable_data: typing.Dict[str, object] = {}
                    settings.setArrayIndex(i)
                    for key in settings.childKeys():
                        editable_data[key] = settings.value(key)
                    editables.append(editable_data)
            if editables:
                for editable in editables:
                    if "Name" in editable:
                        assert isinstance(editable["Name"], str)
                        editable["Reference"] = editable["Name"].replace("-", "/")
                        del editable["Name"]
                    if "Path" in editable:
                        # this is wrong for managed SCM editables, as the path stored
                        # is relative and there's no way to convert it to an absolute
                        # path as now needed this bits that will go wrong is any
                        # workspace related action in manage editables
                        editable["RecipePath"] = editable["Path"]
                        del editable["Path"]
                settings.remove("Editables")
                with SettingsWriteArray(settings, "Editables", len(editables)):
                    for i, editable in enumerate(editables):
                        settings.setArrayIndex(i)
                        for key, value in editable.items():
                            settings.setValue(key, value)


def _patch_settings_from_v3(settings: QtCore.QSettings) -> None:
    """
    This patch adds a name key to each extra profiles dir for a local cache.
    """
    settings = BaseSettings.make_settings()
    with SettingsReadArray(settings, "Conan/LocalCaches") as cache_array:
        for i in range(cache_array.size):
            settings.setArrayIndex(i)
            with SettingsReadArray(settings, "ExtraProfileDirs") as profiledirs_array:
                extra_dirs = []
                for j in range(profiledirs_array.size):
                    settings.setArrayIndex(j)
                    extra_dirs.append(settings.value("Path"))
            if profiledirs_array.size > 0:
                assert len(extra_dirs) == 1, "Only upgrading a single extra directory"
                settings.remove("ExtraProfileDirs")
                with SettingsWriteArray(
                    settings,
                    "ExtraProfileDirs",
                    len(extra_dirs),
                ):
                    # if there was an extra directory, it was for Nuke,
                    # so name it as such
                    settings.setArrayIndex(0)
                    settings.setValue(
                        "Path",
                        extra_dirs,
                    )
                    settings.setValue("Name", "Nuke")


def _patch_settings_from_v2(settings: QtCore.QSettings) -> None:
    """
    This patch moves Conan V2 from general to conan settings
    """
    old_key = "ConanV2Mode"
    oldv2mode = settings.value(old_key, None)
    if oldv2mode is not None:
        settings.remove(old_key)
        settings.setValue("Conan/V2Mode", oldv2mode)


def _patch_settings_from_v1(settings: QtCore.QSettings) -> None:
    """
    This patch moves editables from a separate group to under the recipe.
    """
    editable_groups = [k for k in settings.childGroups() if k.endswith("-editables")]
    editable_data: typing.Dict[str, typing.List[typing.Dict[str, typing.Any]]] = {}
    for editable_group in editable_groups:
        uuid_str = str(editable_group).replace("-editables", "")
        editable_data[uuid_str] = []
        with SettingsReadArray(settings, editable_group) as array:
            for i in range(array.size):
                settings.setArrayIndex(i)
                per_editable_settings = {}
                keys = settings.allKeys()
                for key in keys:
                    per_editable_settings[key] = settings.value(key)
                editable_data[uuid_str].append(per_editable_settings)
        settings.remove(editable_group)
    for editable_uuid_str, editable_array in editable_data.items():
        group = f"Recipe/{editable_uuid_str}"
        with SettingsGroup(settings, group), SettingsWriteArray(
            settings, "Editables", len(editable_array)
        ):
            for i, editable_dict in enumerate(editable_array):
                settings.setArrayIndex(i)
                for key, value in editable_dict.items():
                    settings.setValue(key, value)


def _patch_settings_from_v0(settings: QtCore.QSettings) -> None:
    # pylint: disable=too-many-locals, too-many-branches
    """
    This patch:
    1) Removes the %General group
    2) converts the QVariant versions of QUuids into strings.
       This applies to values in recent recipes, and keys in recipe settings,
       and keys in editables.
    """
    # move the old general group out into the un-grouped General
    with SettingsGroup(settings, "General"):
        general_settings = {}
        for key in settings.allKeys():
            general_settings[key] = settings.value(key)
    settings.remove("General")
    for key, value in general_settings.items():
        settings.setValue(key, value)
    # recent recipe uuids
    recent_recipes = []
    with SettingsReadArray(settings, "RecentRecipes") as array:
        recent_recipes_size = array.size
        for i in range(recent_recipes_size):
            settings.setArrayIndex(i)
            path = settings.value("Path")
            uuid = settings.value("UUID")
            recent_recipes.append((path, uuid))
    settings.remove("RecentRecipes")
    if recent_recipes_size > 0:
        with SettingsWriteArray(settings, "RecentRecipes", recent_recipes_size):
            for i in range(recent_recipes_size):
                settings.setArrayIndex(i)
                settings.setValue("Path", recent_recipes[i][0])
                assert isinstance(recent_recipes[i][1], QtCore.QUuid)
                settings.setValue(
                    "UUID",
                    recent_recipes[i][1].toString(  # type: ignore
                        QtCore.QUuid.WithoutBraces
                    ),
                )
    # recipe settings
    recipe_settings: typing.Dict[str, typing.Dict[str, typing.Any]] = {}
    with SettingsGroup(settings, "Recipe"):
        uuids = set(settings.childGroups())
        prefix = "QtCore.QUuid('{"
        suffix = "}')"
        for uuid in uuids:
            uuid_str = uuid[len(prefix) : -len(suffix)]  # noqa: E203
            recipe_settings[uuid_str] = {}
            with SettingsGroup(settings, uuid):
                keys = settings.allKeys()
                for key in keys:
                    recipe_settings[uuid_str][key] = settings.value(key)
    settings.remove("Recipe")
    with SettingsGroup(settings, "Recipe"):
        for uuid_str, uuid_dict in recipe_settings.items():
            for key, value in uuid_dict.items():
                settings.setValue(f"{uuid_str}/{key}", value)
    # editables
    suffix = "}')-editables"
    editable_settings: typing.Dict[str, typing.List[typing.Dict[str, typing.Any]]] = {}
    editable_groups = [
        group for group in settings.childGroups() if group.endswith("-editables")
    ]
    for editable in editable_groups:
        uuid_str = editable[len(prefix) : -len(suffix)]  # noqa: E203
        editable_settings[uuid_str] = []
        with SettingsReadArray(settings, editable) as array:
            for i in range(array.size):
                settings.setArrayIndex(i)
                per_editable_settings = {}
                keys = settings.allKeys()
                for key in keys:
                    per_editable_settings[key] = settings.value(key)
                editable_settings[uuid_str].append(per_editable_settings)
        settings.remove(editable)
    for editable_uuid, editable_data in editable_settings.items():
        with SettingsWriteArray(
            settings, f"{editable_uuid}-editables", len(editable_data)
        ):
            for i, data in enumerate(editable_data):
                settings.setArrayIndex(i)
                for key, value in data.items():
                    settings.setValue(key, value)


def _backup_settings(settings: QtCore.QSettings) -> None:
    filename = pathlib.Path(settings.fileName())
    backup_filename = f"{filename.name}.{time.strftime('%Y%m%d-%H%M%S')}.bk"
    backup_path = filename.parent / backup_filename
    shutil.copyfile(filename, backup_path)


def update_settings_to_current_version() -> None:
    """
    Upgrade settings to the latest version, incrementally
    """
    settings = BaseSettings.make_settings()
    if len(settings.allKeys()) > 0:
        version = settings.value("SettingsVersion", 0, type=int)
        assert isinstance(version, int)
        if version < CURRENT_SETTINGS_VERSION:
            _backup_settings(settings)
            while version < CURRENT_SETTINGS_VERSION:
                patch_function = globals()[f"_patch_settings_from_v{version}"]
                patch_function(settings)
                version += 1
    settings.setValue("SettingsVersion", CURRENT_SETTINGS_VERSION)
