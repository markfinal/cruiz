#!/usr/bin/env python3

"""
Settings context manager for GraphViz preferences
"""

import typing

from .basesettings import (
    BaseSettings,
    StringSetting,
    ComparableCommonSettings,
    SettingMeta,
)
from .writermixin import _WriterMixin
from .valueclasses import ScalarValue


class GraphVizSettings(ComparableCommonSettings):
    """
    Representation of GraphViz settings
    """

    def __init__(self) -> None:
        self._property_meta = {
            "bin_directory": SettingMeta("BinDir", StringSetting, None, ScalarValue),
        }

    @property
    def bin_directory(self) -> StringSetting:
        """
        Get the GraphViz bin directory
        """
        return self._get_value_via_meta()

    @bin_directory.setter
    def bin_directory(self, value: str) -> None:
        self._set_value_via_meta(value)


class GraphVizSettingsReader:
    """
    Context manager for reading GraphViz settings from disk
    """

    def __init__(self) -> None:
        self.group = "Thirdparty/GraphViz"
        self.settings = BaseSettings.make_settings()

    def __enter__(self) -> GraphVizSettings:
        self.settings.beginGroup(self.group)
        self._settings_object = GraphVizSettings()
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


class GraphVizSettingsWriter(_WriterMixin):
    """
    Utility class for writing changed GraphViz settings to disk
    """

    def __init__(self) -> None:
        self._reader_for_writer = GraphVizSettingsReader()
