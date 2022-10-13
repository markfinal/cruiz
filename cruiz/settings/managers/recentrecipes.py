#!/usr/bin/env python3

"""
Settings context manager for recent recipes
"""

import typing

from qtpy import QtCore

from .basesettings import BaseSettings, CommonSettings


# TODO CommonSettings not all used
class RecentRecipeSettings(CommonSettings):
    """
    Settings for recent recipes
    """

    def uuids(self) -> typing.List[QtCore.QUuid]:
        """
        Get the list of UUIDs for the recent recipes.
        """
        result: typing.List[QtCore.QUuid] = []
        assert self.settings_reader
        settings = self.settings_reader.settings
        for i in range(self.settings_reader.count):
            settings.setArrayIndex(i)
            result.append(QtCore.QUuid(settings.value("UUID")))
        return result


class RecentRecipeSettingsReader:
    """
    Context manager for reading recent recipes from disk.
    """

    def __init__(self) -> None:
        self.group = ""
        self._array = "RecentRecipes"
        self.settings = BaseSettings.make_settings()
        self.count = 0

    def __enter__(self) -> RecentRecipeSettings:
        self.count = self.settings.beginReadArray(self._array)
        self._settings_object = RecentRecipeSettings()
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


class RecentRecipeSettingsWriter:  # TODO: should this derive from _WriterMixin?
    """
    Context manager for writing recent recipes to disk
    """

    def __init__(self) -> None:
        self._reader_for_writer = RecentRecipeSettingsReader()
        self._array = "RecentRecipes"

    def make_current(self, uuid: QtCore.QUuid) -> bool:
        """
        Make the specified recipe current
        """
        with self._reader_for_writer as settings:
            current_list = settings.uuids()
        uuid_exists = uuid in current_list
        # always make the current recipe the first in the list
        if uuid_exists:
            current_list.remove(uuid)
        current_list.insert(0, uuid)
        with BaseSettings.WriteArray(
            self._array, replace=True
        ) as settings:  # TODO: can this use the reader's QSettings?
            for i, uuid in enumerate(current_list):
                settings.setArrayIndex(i)
                settings.setValue("UUID", uuid.toString(QtCore.QUuid.WithoutBraces))
        return uuid_exists


class RecentRecipeSettingsDeleter:
    """
    Context manager for deleting a recent recipe
    """

    def __init__(self) -> None:
        self._reader_for_deleter = RecentRecipeSettingsReader()
        self._array = "RecentRecipes"

    def delete(self, uuid: QtCore.QUuid) -> None:
        """
        Delete the recent recipe represented by UUID
        """
        with self._reader_for_deleter as settings:
            current_list = settings.uuids()
        current_list = [u for u in current_list if u != uuid]
        BaseSettings.make_settings().remove(self._array)
        if current_list:
            with BaseSettings.WriteArray(self._array) as settings:
                for i, uuid in enumerate(current_list):
                    settings.setArrayIndex(i)
                    settings.setValue("UUID", uuid.toString(QtCore.QUuid.WithoutBraces))
