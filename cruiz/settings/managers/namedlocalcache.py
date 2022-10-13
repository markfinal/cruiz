#!/usr/bin/env python3

"""
Settings context manager for named local caches
"""

from __future__ import annotations

import typing

from cruiz.interop.pod import ExtraProfileDirectory

from .writermixin import _WriterMixin
from .valueclasses import ScalarValue, DictValue, ListValue

from .basesettings import (
    BaseSettings,
    StringSetting,
    DictSetting,
    CommonSettings,
    SettingMeta,
    ListSetting,
)


# TODO: this needs some work as there is a lot of repetition


class NamedLocalCacheSettings(CommonSettings):
    """
    Settings for named local caches.
    """

    def __init__(self) -> None:
        self._property_meta = {
            "home_dir": SettingMeta("Dir", StringSetting, None, ScalarValue),
            "short_home_dir": SettingMeta("ShortDir", StringSetting, None, ScalarValue),
            "environment_added": SettingMeta("Environment", DictSetting, {}, DictValue),
            "environment_removed": SettingMeta(
                "EnvironmentRemoved", ListSetting, [], ListValue
            ),
            "extra_profile_directories": SettingMeta(
                "ExtraProfileDirs", DictSetting, {}, DictValue
            ),
        }

    # TODO: this is a bit weird, should it be a function?
    # Also, current uses of this function only check to see its length
    @property
    def recipe_uuids(self) -> typing.List[str]:
        """
        Return list of UUIDs for the recipes in this cache.
        """
        results: typing.List[str] = []
        settings = BaseSettings.make_settings()
        assert self.settings_reader
        settings.beginGroup("Recipe")
        for uuid in settings.childGroups():
            if (
                settings.value(f"{uuid}/LocalCacheName")
                == self.settings_reader.cache_name
            ):
                results.append(uuid)
        settings.endGroup()
        return results

    @property
    def home_dir(self) -> StringSetting:
        """
        Return the home directory of this cache.
        """
        return self._get_value_via_meta()

    @home_dir.setter
    def home_dir(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def short_home_dir(self) -> StringSetting:
        """
        Return the short home directory of this cache.
        """
        return self._get_value_via_meta()

    @short_home_dir.setter
    def short_home_dir(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def environment_added(self) -> DictSetting:
        """
        Return the added environment dictionary for this cache.
        """
        assert self.settings_reader
        settings = self.settings_reader.settings
        key = "Environment"
        env: typing.Dict[str, str] = {}
        with BaseSettings.ReadArray(key, settings=settings) as (settings, count):
            for i in range(count):
                settings.setArrayIndex(i)
                name = str(settings.value("Name"))
                value = str(settings.value("Value"))
                env[name] = value
        return DictSetting(env, {})

    def environment_added_at(self, row_index: int) -> typing.Tuple[str, str]:
        """
        Get the key-value pair at the specified index.
        """
        assert self.settings_reader
        settings = self.settings_reader.settings
        key = "Environment"
        with BaseSettings.ReadArray(key, settings=settings) as (settings, count):
            settings.setArrayIndex(row_index)
            name = str(settings.value("Name"))
            value = str(settings.value("Value"))
            return name, value

    @property
    def environment_removed(self) -> ListSetting:
        """
        Return the removed environment keys for this cache.
        """
        assert self.settings_reader
        settings = self.settings_reader.settings
        key = "EnvironmentRemoved"
        env_removed: typing.List[str] = []
        with BaseSettings.ReadArray(key, settings=settings) as (settings, count):
            for i in range(count):
                settings.setArrayIndex(i)
                name = str(settings.value("Name"))
                env_removed.append(name)
        return ListSetting(env_removed, [])

    def sync_env_changes(
        self,
        existing_removed: typing.List[str],
        changes: _EnvChangeManagement,
    ) -> None:
        """
        Synchronise the changes environment into the NamedLocalCacheSettings
        ready to be written back to disk.

        The existing 'removed' environment keys are provided here because it's a list
        which must always be provided in full.
        """
        assert changes.has_change
        if changes.add_required or changes.add_clear:
            env_added: typing.Dict[str, typing.Optional[str]] = {}
            if changes.add_required:
                env_added.update(changes.add_required)
            for key in changes.add_clear:
                env_added[key] = None
            # avoids private name mangling
            setattr(  # noqa: B010
                self,
                "__environment_added",
                DictValue(
                    env_added, "environment_added", "Environment", "Name", "Value"
                ),
            )
        if changes.remove_required or changes.remove_clear:
            if changes.remove_required:
                existing_removed.extend(changes.remove_required)
            for key in changes.remove_clear:
                existing_removed.remove(key)
            # avoids private name mangling
            setattr(  # noqa: B010
                self,
                "__environment_removed",
                ListValue(
                    existing_removed,
                    "environment_removed",
                    "EnvironmentRemoved",
                    "Name",
                ),
            )

    @property
    def extra_profile_directories(self) -> DictSetting:
        """
        Return extra profile directories for this cache.
        """
        assert self.settings_reader
        settings = self.settings_reader.settings
        key = "ExtraProfileDirs"
        dirs: typing.Dict[str, str] = {}
        with BaseSettings.ReadArray(key, settings=settings) as (settings, count):
            for i in range(count):
                settings.setArrayIndex(i)
                name = str(settings.value("Name"))
                value = str(settings.value("Path"))
                dirs[name] = value
        return DictSetting(dirs, {})

    def append_extra_profile_directories(
        self, extra_dir: ExtraProfileDirectory
    ) -> None:
        """
        Append new extra profile directories

        self.__extra_profile_directories set at the end of the function,
        but in case this is called several times, read at the start too
        """
        try:
            (
                existing_extra_profile_dirs,
                prop,
                real_key,
            ) = self.__extra_profile_directories  # type: ignore
        except AttributeError:
            existing_extra_profile_dirs = {}
            prop = "extra_profile_directories"
            real_key = "ExtraProfileDirs"
        existing_extra_profile_dirs[extra_dir.name] = extra_dir.directory
        # avoids private name mangling
        setattr(  # noqa: B010
            self,
            "__extra_profile_directories",
            DictValue(existing_extra_profile_dirs, prop, real_key, "Name", "Path"),
        )

    def remove_extra_profile_directories(self, name: str) -> None:
        """
        Append new extra profile directories

        self.__extra_profile_directories set at the end of the function,
        but in case this is called several times, read at the start too
        """
        try:
            (
                existing_extra_profile_dirs,
                prop,
                real_key,
            ) = self.__extra_profile_directories  # type: ignore
        except AttributeError:
            existing_extra_profile_dirs = {}
            prop = "extra_profile_directories"
            real_key = "ExtraProfileDirs"
        existing_extra_profile_dirs[name] = None
        # avoids private name mangling
        setattr(  # noqa: B010
            self,
            "__extra_profile_directories",
            DictValue(existing_extra_profile_dirs, prop, real_key, "Name", "Path"),
        )


class _EnvChangeManagement:
    """
    Manage the changes (CM) in the requested environment
    """

    def __init__(self) -> None:
        self.add_required: typing.Dict[str, str] = {}
        self.add_clear: typing.List[str] = []
        self.remove_required: typing.List[str] = []
        self.remove_clear: typing.List[str] = []

    def key_required(self, key: str, value: str) -> None:
        """
        The environment key-value pair is required to be used.
        If used on a key that is already stored, the value is overwritten.
        """
        self.add_required[key] = value

    def key_not_required(self, key: str) -> None:
        """
        The environment key is no longer required.
        If added in this CM, it is no longer added.
        Otherwise, it is already in the environment and will be scheduled to be removed.
        """
        if key in self.add_required:
            del self.add_required[key]
        else:
            self.add_clear.append(key)

    def key_never_required(self, key: str) -> None:
        """
        The key is scheduled to not be present in the applied environment.
        """
        self.remove_required.append(key)

    def key_not_never_required(self, key: str) -> None:
        """
        If the key was scheduled in this CM not to be present, this is undone.
        Otherwise, the key will no longer be removed.
        """
        if key in self.remove_required:
            self.remove_required.remove(key)
        else:
            self.remove_clear.append(key)

    @property
    def has_change(self) -> bool:
        """
        Determine whether any change management is required.
        """
        return (
            bool(self.add_required)
            or bool(self.add_clear)
            or bool(self.remove_required)
            or bool(self.remove_clear)
        )


class NamedLocalCacheSettingsReader:
    """
    Context manager reader for named local cache settings.
    """

    def __init__(self, cache_name: str) -> None:
        self.cache_name = cache_name
        self.group = BaseSettings._location_of_key_value_pair(
            "Conan/LocalCaches", "Name", cache_name
        )
        self.settings = BaseSettings.make_settings()

    def __enter__(self) -> NamedLocalCacheSettings:
        self.settings.beginGroup(self.group)
        self._settings_object = NamedLocalCacheSettings()
        self._settings_object.settings_reader = self
        return self._settings_object

    def __exit__(
        self, exc_type: typing.Any, exc_value: typing.Any, exc_traceback: typing.Any
    ) -> typing.Any:
        self.settings.endGroup()
        self._settings_object.settings_reader = None
        del self._settings_object
        if exc_type is None:
            pass
        else:
            # propagate exception
            return False


class NamedLocalCacheSettingsWriter(_WriterMixin):
    """
    Context manager to write named local cache settings to disk.
    """

    def __init__(self, name: str) -> None:
        self._reader_for_writer = NamedLocalCacheSettingsReader(name)


class AllNamedLocalCacheSettingsReader:
    """
    Context manager for returning the names of all local caches.
    """

    def __init__(self) -> None:
        self._settings = BaseSettings.make_settings()

    def __enter__(self) -> typing.List[str]:
        all_names: typing.List[str] = []
        size = self._settings.beginReadArray("Conan/LocalCaches")
        for i in range(size):
            self._settings.setArrayIndex(i)
            all_names.append(str(self._settings.value("Name")))
        self._settings.endArray()
        return all_names

    def __exit__(
        self, exc_type: typing.Any, exc_value: typing.Any, exc_traceback: typing.Any
    ) -> typing.Any:
        return False


class NamedLocalCacheDeleter:
    """
    Delete a named local cache.
    """

    def __init__(self) -> None:
        self._group = "Conan"
        self._settings = BaseSettings.make_settings()

    def delete(self, name: str) -> None:
        """
        Delete the named local cache from settings.
        """
        caches: typing.List[typing.Dict[str, object]] = []
        with BaseSettings.ReadArray(f"{self._group}/LocalCaches", self._settings) as (
            settings,
            count,
        ):
            for i in range(count):
                settings.setArrayIndex(i)
                if settings.value("Name") == name:
                    continue
                keys = settings.childKeys()
                cache = {}
                for key in keys:
                    cache[key] = settings.value(key)
                caches.append(cache)
        assert len(caches) >= 1  # always at least one because of the Default
        with BaseSettings.WriteArray(
            f"{self._group}/LocalCaches", replace=True, settings=self._settings
        ) as settings:
            for i, cache_data in enumerate(caches):
                settings.setArrayIndex(i)
                for key, value in cache_data.items():
                    settings.setValue(key, value)


class NamedLocalCacheCreator:
    """
    Create a named local cache.
    """

    def __init__(self) -> None:
        self._group = "Conan/LocalCaches"
        self._settings = BaseSettings.make_settings()

    def create(
        self,
        name: str,
        home_dir: typing.Optional[str],
        short_home_dir: typing.Optional[str],
    ) -> None:
        """
        Create the named local cache from settings.
        """
        with BaseSettings.ReadArray(self._group, self._settings) as (_, count):
            pass
        with BaseSettings.WriteArray(self._group, settings=self._settings) as settings:
            settings.setArrayIndex(count)
            settings.setValue("Name", name)
            settings.setValue("Dir", home_dir or None)
            settings.setValue("ShortDir", short_home_dir or None)
