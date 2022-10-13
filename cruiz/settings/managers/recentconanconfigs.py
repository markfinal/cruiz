#!/usr/bin/env python3

"""
Settings context manager for recent Conan configurations
"""

import typing

from .basesettings import BaseSettings, ListSetting, CommonSettings, SettingMeta
from .writermixin import _WriterMixin
from .valueclasses import ListValue


# TODO: CommonSettings isn't completely used
class RecentConanConfigSettings(CommonSettings):
    """
    Settings representing the recent Conan configurations visited
    """

    def __init__(self) -> None:
        self._property_meta = {
            "paths": SettingMeta("RecentConanConfigs", ListSetting, [], ListValue),
        }

    @property
    def paths(self) -> ListSetting:
        """
        Get the paths of the Conan configurations visited
        """
        result: typing.List[str] = []
        assert self.settings_reader
        settings = self.settings_reader.settings
        # TODO: remove count on the reader, and replace by
        # num child groups / keys per entry in array
        assert self.settings_reader.count == (
            len(self.settings_reader.settings.childGroups()) / 1
        )
        for i in range(self.settings_reader.count):
            settings.setArrayIndex(i)
            result.append(str(settings.value("Path")))
        return ListSetting(result, [])

    @paths.setter
    def paths(self, paths: typing.List[str]) -> None:
        """
        Set the list of paths used for Conan configurations.
        """
        # avoids private name mangling
        setattr(  # noqa: B010
            self, "__new_paths", ListValue(paths, "paths", "RecentConanConfigs", "Path")
        )


class RecentConanConfigSettingsReader:
    """
    Context manager to read recent Conan configurations from disk
    """

    def __init__(self) -> None:
        self.group = ""
        self.array = "RecentConanConfigs"
        self.settings = BaseSettings.make_settings()
        self.count = 0

    def __enter__(self) -> RecentConanConfigSettings:
        self.count = self.settings.beginReadArray(self.array)
        self._settings_object = RecentConanConfigSettings()
        self._settings_object.settings_reader = self
        return self._settings_object

    def __exit__(
        self, exc_type: typing.Any, exc_value: typing.Any, exc_traceback: typing.Any
    ) -> typing.Any:
        self.settings.endArray()
        self._settings_object.settings_reader = None
        del self._settings_object
        if exc_type is None:
            pass
        else:
            # propagate exception
            return False


class RecentConanConfigSettingsWriter(_WriterMixin):
    """
    Utility class to write recent Conan configurations to disk
    """

    def __init__(self) -> None:
        self._reader_for_writer = RecentConanConfigSettingsReader()


class RecentConanConfigSettingsDeleter:
    """
    Utility class to delete recent Conan configurations from disk settings
    """

    def __init__(self) -> None:
        self._reader_for_deleter = RecentConanConfigSettingsReader()

    def delete(self, path: str) -> None:
        """
        Delete the specified Conan configuration from disk settings
        """
        with self._reader_for_deleter as settings:
            current_list = settings.paths.resolve()
        current_list = [x for x in current_list if x != path]
        BaseSettings.make_settings().remove(self._reader_for_deleter.array)
        if current_list:
            with BaseSettings.WriteArray(
                self._reader_for_deleter.array, replace=True
            ) as settings:
                for i, path in enumerate(current_list):
                    settings.setArrayIndex(i)
                    settings.setValue("Path", path)
