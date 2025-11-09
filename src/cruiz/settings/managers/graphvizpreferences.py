#!/usr/bin/env python3

"""Settings context manager for GraphViz preferences."""

from __future__ import annotations

import typing

from .basesettings import (
    BaseSettings,
    ComparableCommonSettings,
    SettingMeta,
    StringSetting,
)
from .valueclasses import ScalarValue
from .writermixin import _WriterMixin

if typing.TYPE_CHECKING:
    import types


class GraphVizSettings(ComparableCommonSettings):
    """Representation of GraphViz settings."""

    def __init__(self) -> None:
        """Initialise a GraphVizSettings."""
        super().__init__()
        self._property_meta = {
            "bin_directory": SettingMeta("BinDir", StringSetting, None, ScalarValue),
        }

    @property
    def bin_directory(self) -> StringSetting:
        """Get the GraphViz bin directory."""
        return self._get_value_via_meta()

    @bin_directory.setter
    def bin_directory(self, value: str) -> None:
        self._set_value_via_meta(value)


class GraphVizSettingsReader:
    """Context manager for reading GraphViz settings from disk."""

    def __init__(self) -> None:
        """Initialise a GraphVizSettingsReader."""
        self.group = "Thirdparty/GraphViz"
        self.settings = BaseSettings.make_settings()

    def __enter__(self) -> GraphVizSettings:
        """Enter a context manager with a GraphVizSettingsReader."""
        self.settings.beginGroup(self.group)
        self._settings_object = GraphVizSettings()
        self._settings_object.settings_reader = self
        return self._settings_object

    def __exit__(
        self,
        exc_type: typing.Optional[type[BaseException]],
        exc_value: typing.Optional[BaseException],
        exc_traceback: types.TracebackType,
    ) -> typing.Any:
        """Exit a context manager with a GraphVizSettingsReader."""
        self.settings.endGroup()
        self._settings_object.settings_reader = None
        del self._settings_object
        if exc_type is not None:
            # propagate exception
            return False
        return True


class GraphVizSettingsWriter(_WriterMixin):
    """Utility class for writing changed GraphViz settings to disk."""

    def __init__(self) -> None:
        """Initialise a GraphVizSettingsWriter."""
        self._reader_for_writer = GraphVizSettingsReader()
