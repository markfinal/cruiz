#!/usr/bin/env python3

"""
Settings base classes
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import inspect
import typing

from qtpy import QtCore, QtGui


@dataclass
class SettingMeta:
    settings_key: str
    type: typing.Type[typing.Any]
    default_value: typing.Any
    save_type: typing.Type[typing.Any]


@dataclass
class StringSetting:
    """
    Representation of a string value from disk settings and its fallback
    """

    value: typing.Optional[str]
    fallback: str

    def resolve(self) -> str:
        """
        If a value exists on disk, return that, otherwise return the fallback.
        """
        if self.value is None:
            return self.fallback
        return self.value


@dataclass
class IntSetting:
    """
    Representation of an integer value from disk settings and its fallback
    """

    value: typing.Optional[int]
    fallback: int

    def resolve(self) -> int:
        """
        If a value exists on disk, return that, otherwise return the fallback.
        """
        if self.value is None:
            return self.fallback
        return self.value


@dataclass
class BoolSetting:
    """
    Representation of a Boolean value from disk settings and its fallback
    """

    value: typing.Optional[bool]
    fallback: bool

    def resolve(self) -> bool:
        """
        If a value exists on disk, return that, otherwise return the fallback.
        """
        if self.value is None:
            return self.fallback
        return self.value


@dataclass
class ColourSetting:
    """
    Representation of a QColor value from disk settings and its fallback
    """

    value: typing.Optional[QtGui.QColor]
    fallback: QtGui.QColor

    def resolve(self) -> QtGui.QColor:
        """
        If a value exists on disk, return that, otherwise return the fallback.
        """
        if self.value is None:
            return self.fallback
        return self.value


@dataclass
class DictSetting:
    """
    Representation of a dictionary from disk settings and its fallback
    """

    value: typing.Optional[typing.Dict[str, str]]
    fallback: typing.Dict[str, str]

    def resolve(self) -> typing.Dict[str, str]:
        """
        If a value exists on disk, return that, otherwise return the fallback.
        """
        if self.value is None:
            return self.fallback
        return self.value

    def __getitem__(self, name: str) -> str:
        assert self.value
        return self.value[name]

    def __setitem__(self, name: str, value: str) -> None:
        assert self.value
        self.value[name] = value

    def __delitem__(self, name: str) -> None:
        assert self.value
        del self.value[name]


@dataclass
class ListSetting:
    """
    Representation of a list from disk settings and its fallback
    """

    value: typing.Optional[typing.List[str]]
    fallback: typing.List[str]

    def resolve(self) -> typing.List[str]:
        """
        If a value exists on disk, return that, otherwise return the fallback.
        """
        if self.value is None:
            return self.fallback
        return self.value


# TODO: does this need renaming?
class WorkflowCwd(IntEnum):
    """
    Supported current working directories in workflow
    """

    RELATIVE_TO_RECIPE = 0
    RELATIVE_TO_GIT = 1


@dataclass
class WorkflowCwdSetting:
    """
    Setting value representing the enum WorkflowCwd, with a fallback
    """

    value: typing.Optional[WorkflowCwd]
    fallback: WorkflowCwd

    def resolve(self) -> WorkflowCwd:
        """
        Resolve the setting value, either the current value or the fallback
        """
        return self.value or self.fallback


class BaseSettings:
    """
    Common settings functionality
    """

    @staticmethod
    def make_settings() -> QtCore.QSettings:
        """
        Make a QSettings instance to operate on settings.
        """
        # since there is a central location to where the QSettings
        # is constructed, override the meanings of the argument to make
        # a sensible path to the preferences file
        return QtCore.QSettings(
            QtCore.QSettings.IniFormat,
            QtCore.QSettings.UserScope,
            "cruiz",  # org name
            "preferences",  # application name
        )

    @staticmethod
    def _location_of_key_value_pair(array_key: str, key: str, value: str) -> str:
        with BaseSettings.ReadArray(array_key) as (settings, size):
            for i in range(size):
                settings.setArrayIndex(i)
                if settings.value(key) == value:
                    return f"{array_key}/{i + 1}"  # settings indices are 1 based
        raise RuntimeError(f"Unable to locate '{key}={value}' in array '{array_key}'")

    class Group:
        """
        Representation of a QSettings group as a context manager
        """

        def __init__(
            self, group: str, settings: typing.Optional[QtCore.QSettings] = None
        ) -> None:
            self._settings = settings or BaseSettings.make_settings()
            self._group = group

        def __enter__(self) -> QtCore.QSettings:
            self._settings.beginGroup(self._group)
            return self._settings

        def __exit__(
            self, exc_type: typing.Any, exc_value: typing.Any, exc_traceback: typing.Any
        ) -> typing.Any:
            self._settings.endGroup()

    class ReadArray:
        """
        Representation of a QSettings array as a context manager
        """

        def __init__(
            self, array: str, settings: typing.Optional[QtCore.QSettings] = None
        ) -> None:
            self._settings = settings or BaseSettings.make_settings()
            self._array = array

        def __enter__(self) -> typing.Tuple[QtCore.QSettings, int]:
            count = self._settings.beginReadArray(self._array)
            return self._settings, count

        def __exit__(
            self, exc_type: typing.Any, exc_value: typing.Any, exc_traceback: typing.Any
        ) -> typing.Any:
            self._settings.endArray()

    # TODO: this is not such an elegant solution when the array to write
    # is empty and replace=True, because a zero-length array is written to the settings,
    # rather than nothing there is insufficient knowledge here to know whether to start
    # writing the array also, beginWriteArray takes a size parameter too, but doesn't
    # here...
    # it's not an exception either to have a zero-length array, so how is it reported
    # back?
    class WriteArray:
        """
        Representation of writing an array to QSettings as a context manager
        """

        def __init__(
            self,
            array: str,
            replace: bool = False,
            settings: typing.Optional[QtCore.QSettings] = None,
        ) -> None:
            self._settings = settings or BaseSettings.make_settings()
            self._array = array
            self._replace = replace

        def __enter__(self) -> QtCore.QSettings:
            if self._replace:
                self._settings.remove(self._array)
            self._settings.beginWriteArray(self._array)
            return self._settings

        def __exit__(
            self, exc_type: typing.Any, exc_value: typing.Any, exc_traceback: typing.Any
        ) -> typing.Any:
            self._settings.endArray()


class CommonSettings:
    """
    Common functionality to all settings classes.

    self._property_meta is expected to be set up in the concrete class
    """

    def __init__(self) -> None:
        self.settings_reader: typing.Optional[typing.Any] = None

    def _get_value_via_meta(self) -> typing.Any:
        """
        Get the value from settings using meta data to determine
        types and settings key
        """
        assert self.settings_reader
        property_name = inspect.getouterframes(inspect.currentframe())[1][3]
        map = self._property_meta[property_name]  # type: ignore
        settings = self.settings_reader.settings
        value = None
        if settings.contains(map.settings_key):
            if map.type == BoolSetting:
                value = settings.value(map.settings_key, type=bool)
            elif map.type in (IntSetting, WorkflowCwdSetting):
                value = settings.value(map.settings_key, type=int)
            else:
                value = settings.value(map.settings_key)
        return map.type(value, map.default_value)

    def _set_value_via_meta(self, value: typing.Any) -> None:
        """
        Set the value into temporary storage before serialising, using
        meta data to know where to read and what to write.
        """
        property_name = inspect.getouterframes(inspect.currentframe())[1][3]
        map = self._property_meta[property_name]  # type: ignore
        value_to_store = map.save_type(value, property_name, map.settings_key)
        attribute_to_store = f"__{property_name}"
        setattr(self, attribute_to_store, value_to_store)


class ComparableCommonSettings(CommonSettings):
    """
    Extended common functionality to settings classes that want to compare their
    current state with that on disk
    """

    def empty(self, reader_context_manager: typing.Any) -> bool:
        """
        Are current settings values different from those on disk?
        """
        keys_to_set = [k for k, _ in self.__dict__.items() if k.startswith("__")]
        if not keys_to_set:
            return True
        # TODO: this obviously has some side-effects, but probably ok
        recheck = False
        with reader_context_manager as settings:
            for key in keys_to_set:
                entry = getattr(self, key)
                value = getattr(settings, entry.property_name)
                # TODO: should this check match the 3-step check in the writer sync()?
                if value.resolve() == entry.value:
                    del self.__dict__[key]
                    recheck = True
        if recheck:
            keys_to_set = [k for k, _ in self.__dict__.items() if k.startswith("__")]
        return not bool(keys_to_set)
