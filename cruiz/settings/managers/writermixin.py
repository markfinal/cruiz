#!/usr/bin/env python3

"""
Mixin for helping to write settings
"""

from enum import Enum

import typing

from qtpy import QtGui

from .basesettings import BaseSettings


class _WriterMixin:
    """
    Mixing class for writing utilities

    self._reader_for_writer defined in the consuming class.
    """

    def sync(self, changes: typing.Any) -> None:
        """
        Synchronise incoming settings changes with those on disk
        """
        assert hasattr(self, "_reader_for_writer")
        keys_to_set = [k for k in changes.__dict__.keys() if k.startswith("__")]
        if not keys_to_set:
            return
        # get current values from settings and fallbacks
        current_values = {}
        assert hasattr(self, "_reader_for_writer")
        with self._reader_for_writer as settings:
            for key in keys_to_set:
                entry = getattr(changes, key)
                current_values[entry.key] = getattr(settings, entry.property_name)
        # delete those values changes to the fallbacks
        # set others
        with BaseSettings.Group(
            self._reader_for_writer.group
        ) as settings:  # TODO: should probably re-use the settings instance
            for key in keys_to_set:
                entry = getattr(changes, key)
                # if entry values vs current values are any of the following, the
                # disk setting can be removed
                # - equal
                # - entry is falsey and the fallback is None
                # - entry ie explicitly None
                if (
                    entry.value == current_values[entry.key].fallback
                    or (not entry.value and current_values[entry.key].fallback is None)
                    or entry.value is None
                ):
                    settings.remove(entry.key)
                else:
                    if isinstance(entry.value, Enum):
                        settings.setValue(entry.key, entry.value.value)
                    elif isinstance(entry.value, (str, bool, int, QtGui.QColor)):
                        settings.setValue(entry.key, entry.value)
                    elif isinstance(entry.value, list):
                        # entry.value is the entire list to write
                        # it is checked for empty above
                        assert entry.value
                        with BaseSettings.WriteArray(
                            entry.key, replace=True, settings=settings
                        ) as settings:
                            for i, value in enumerate(entry.value):
                                settings.setArrayIndex(i)
                                settings.setValue(entry.entry_key, value)
                    elif isinstance(entry.value, dict):
                        # entry.value is a delta, include None values for removal
                        current_values[entry.key].value.update(entry.value)
                        dict_entries_to_write = {
                            k: v
                            for k, v in current_values[entry.key].value.items()
                            if v is not None
                        }
                        if dict_entries_to_write:
                            with BaseSettings.WriteArray(
                                entry.key, replace=True, settings=settings
                            ) as settings:
                                for i, (inner_key, value) in enumerate(
                                    dict_entries_to_write.items()
                                ):
                                    settings.setArrayIndex(i)
                                    settings.setValue(entry.entry_key, inner_key)
                                    settings.setValue(entry.entry_value, value)
                        else:
                            settings.remove(entry.key)
                    else:
                        raise RuntimeError(
                            f"Unknown type of data to save as settings: '{entry.key}' "
                            f"is type '{type(entry.value)}'"
                        )
                delattr(changes, key)
