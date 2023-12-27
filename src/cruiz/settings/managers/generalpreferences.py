#!/usr/bin/env python3

"""
Settings context managers for general preferences
"""

import platform
import typing

from qtpy import QtGui

from .basesettings import (
    BaseSettings,
    BoolSetting,
    StringSetting,
    ColourSetting,
    ComparableCommonSettings,
    SettingMeta,
)
from .writermixin import _WriterMixin
from .valueclasses import ScalarValue


class GeneralSettings(ComparableCommonSettings):
    """
    Representation of 'general' disk settings
    """

    def __init__(self) -> None:
        super().__init__()

        default_stdout_batching_value = platform.system() == "Windows"

        self._property_meta = {
            "clear_panes": SettingMeta("ClearPanes", BoolSetting, True, ScalarValue),
            "combine_panes": SettingMeta(
                "CombinePanes", BoolSetting, True, ScalarValue
            ),
            "use_stdout_batching": SettingMeta(
                "UseStdoutBatching",
                BoolSetting,
                default_stdout_batching_value,
                ScalarValue,
            ),
            "enable_command_timing": SettingMeta(
                "EnableCommandTimings", BoolSetting, False, ScalarValue
            ),
            "use_compact_look": SettingMeta(
                "UseCompactLook", BoolSetting, False, ScalarValue
            ),
            "default_recipe_directory": SettingMeta(
                "DefaultRecipeDirectory", StringSetting, None, ScalarValue
            ),
            "default_recipe_editor": SettingMeta(
                "DefaultRecipeEditor", StringSetting, None, ScalarValue
            ),
            "busy_icon_colour": SettingMeta(
                "BusyIconColour",
                ColourSetting,
                QtGui.QColor(QtGui.Qt.black),
                ScalarValue,
            ),
            "found_text_background_colour": SettingMeta(
                "FoundTextBackgroundColour",
                ColourSetting,
                QtGui.QColor(QtGui.Qt.GlobalColor.green),
                ScalarValue,
            ),
            "new_recipe_loading_behaviour": SettingMeta(
                "NewLoadingBehaviour", BoolSetting, False, ScalarValue
            ),
        }

    @property
    def clear_panes(self) -> BoolSetting:
        """
        Get whether output panes are cleared on each command
        """
        return self._get_value_via_meta()

    @clear_panes.setter
    def clear_panes(self, value: bool) -> None:
        self._set_value_via_meta(value)

    @property
    def combine_panes(self) -> BoolSetting:
        """
        Get whether output and error panes are combined
        """
        return self._get_value_via_meta()

    @combine_panes.setter
    def combine_panes(self, value: bool) -> None:
        self._set_value_via_meta(value)

    @property
    def use_stdout_batching(self) -> BoolSetting:
        """
        Get whether standard output and error streamed are batched before displaying
        """
        return self._get_value_via_meta()

    @use_stdout_batching.setter
    def use_stdout_batching(self, value: bool) -> None:
        self._set_value_via_meta(value)

    @property
    def enable_command_timing(self) -> BoolSetting:
        """
        Get whether command wallclock timing is enabled
        """
        return self._get_value_via_meta()

    @enable_command_timing.setter
    def enable_command_timing(self, value: bool) -> None:
        self._set_value_via_meta(value)

    @property
    def use_compact_look(self) -> BoolSetting:
        """
        Get whether a compact look is enabled.
        OBSOLETE
        """
        return self._get_value_via_meta()

    @use_compact_look.setter
    def use_compact_look(self, value: bool) -> None:
        self._set_value_via_meta(value)

    @property
    def default_recipe_directory(self) -> StringSetting:
        """
        Get the default recipe directory to look for recipes to load
        """
        return self._get_value_via_meta()

    @default_recipe_directory.setter
    def default_recipe_directory(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def default_recipe_editor(self) -> StringSetting:
        """
        Get the default recipe editor to open recipes in.
        """
        return self._get_value_via_meta()

    @default_recipe_editor.setter
    def default_recipe_editor(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def busy_icon_colour(self) -> ColourSetting:
        """
        Get the colour of the busy icon
        """
        return self._get_value_via_meta()

    @busy_icon_colour.setter
    def busy_icon_colour(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def found_text_background_colour(self) -> ColourSetting:
        """
        Get the background colour of found text.
        """
        return self._get_value_via_meta()

    @found_text_background_colour.setter
    def found_text_background_colour(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def new_recipe_loading_behaviour(self) -> BoolSetting:
        """
        Get whether the new recipe loading behaviour is enabled.
        OSBOLETE
        """
        return self._get_value_via_meta()

    @new_recipe_loading_behaviour.setter
    def new_recipe_loading_behaviour(self, value: str) -> None:
        self._set_value_via_meta(value)


class GeneralSettingsReader:
    """
    Context manager to read from disk settings
    """

    def __init__(self) -> None:
        self.settings = BaseSettings.make_settings()
        self.group = ""

    def __enter__(self) -> GeneralSettings:
        self.settings.beginGroup(self.group)
        self._settings_object = GeneralSettings()
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


class GeneralSettingsWriter(_WriterMixin):
    """
    Utility class for writing changed settings to disk
    """

    def __init__(self) -> None:
        self._reader_for_writer = GeneralSettingsReader()
