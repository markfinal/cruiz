#!/usr/bin/env python3

"""
Settings context manager for recent Conan remotes
"""

import typing

from .basesettings import BaseSettings, CommonSettings, ListSetting, SettingMeta
from .valueclasses import ListValue
from .writermixin import _WriterMixin


# TODO: CommonSettings not all used
class RecentConanRemotesSettings(CommonSettings):
    """
    Settings representing recent Conan remotes
    """

    def __init__(self) -> None:
        self._property_meta = {
            "urls": SettingMeta("RecentConanRemotes", ListSetting, [], ListValue),
        }

    @property
    def urls(self) -> ListSetting:
        """
        Get all the URLs representing the Conan remotes
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
            result.append(str(settings.value("URL")))
        return ListSetting(result, [])

    @urls.setter
    def urls(self, urls: typing.List[str]) -> None:
        """
        Set the URLs used for Conan remotes.
        """
        # avoids private name mangling
        setattr(  # noqa: B010
            self, "__new_urls", ListValue(urls, "urls", "RecentConanRemotes", "URL")
        )


class RecentConanRemotesSettingsReader:
    """
    Context manager for reading recent Conan remotes from disk settings
    """

    def __init__(self) -> None:
        self.group = ""
        self.array = "RecentConanRemotes"
        self.settings = BaseSettings.make_settings()
        self.count = 0

    def __enter__(self) -> RecentConanRemotesSettings:
        self.count = self.settings.beginReadArray(self.array)
        self._settings_object = RecentConanRemotesSettings()
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


class RecentConanRemotesSettingsWriter(_WriterMixin):
    """
    Utility for writing changed recent Conan remote settings to disk
    """

    def __init__(self) -> None:
        self._reader_for_writer = RecentConanRemotesSettingsReader()


class RecentConanRemotesSettingsDeleter:
    """
    Utility for deleting the named recent Conan remote from disk settings
    """

    def __init__(self) -> None:
        self._reader_for_deleter = RecentConanRemotesSettingsReader()

    def delete(self, url: str) -> None:
        """
        Delete a specific recent Conan remote URL from disk settings
        """
        with self._reader_for_deleter as settings:
            current_list = settings.urls.resolve()
        current_list = [x for x in current_list if x != url]
        BaseSettings.make_settings().remove(self._reader_for_deleter.array)
        if current_list:
            with BaseSettings.WriteArray(self._reader_for_deleter.array) as settings:
                for i, path in enumerate(current_list):
                    settings.setArrayIndex(i)
                    settings.setValue("URL", path)
