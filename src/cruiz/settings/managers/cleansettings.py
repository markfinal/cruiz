#!/usr/bin/env python3

"""Settings cleanup."""

import pathlib

from qtpy import QtCore, QtWidgets

from .basesettings import BaseSettings
from .recentrecipes import RecentRecipeSettingsDeleter, RecentRecipeSettingsWriter
from .recipe import RecipeSettingsDeleter


def sanitise_settings(widget: QtWidgets.QWidget) -> bool:
    """
    Sanitise settings to fix oddities.

    Returns True if the settings were modified, False otherwise.
    """
    incomplete_uuids = {}
    recipe_no_longer_exists_uuid = {}
    recent_recipe_only = []
    with BaseSettings.Group("Recipe") as settings:
        all_uuids = settings.childGroups()
        for uuid in all_uuids:
            with BaseSettings.Group(uuid, settings):
                local_cache = settings.value("LocalCacheName", None)
                if local_cache is None:
                    incomplete_uuids[uuid] = "No local cache name in settings"
                    continue
                profile = settings.value("Profile", None)
                if profile is None:
                    incomplete_uuids[uuid] = "No profile in settings"
                    continue
                path = settings.value("Path", None)
                if path is None:
                    incomplete_uuids[uuid] = "No recipe path in settings"
                    continue
                assert isinstance(path, str)
                path = pathlib.Path(path)
                if not path.exists():
                    recipe_no_longer_exists_uuid[uuid] = path
    with BaseSettings.ReadArray("RecentRecipes", settings) as (_, count):
        for i in range(count):
            settings.setArrayIndex(i)
            recent_uuid = settings.value("UUID", None)
            assert isinstance(recent_uuid, str)
            if recent_uuid in all_uuids:
                all_uuids.remove(recent_uuid)
            else:
                recent_recipe_only.append(recent_uuid)
    cleaned = False
    if incomplete_uuids:
        message = "Incomplete recipe settings:\n"
        for uuid, reason in incomplete_uuids.items():
            message += f"{uuid}: {reason}\n"
        message += "Clean?"
        response = QtWidgets.QMessageBox.question(
            widget,
            "Inconsistent recipe settings",
            message,
            button0=QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
            button1=QtWidgets.QMessageBox.StandardButton.Yes,
        )
        if response == QtWidgets.QMessageBox.StandardButton.Yes:
            for uuid in incomplete_uuids:
                real_uuid = QtCore.QUuid(uuid)
                RecipeSettingsDeleter().delete(real_uuid)
                RecentRecipeSettingsDeleter().delete(real_uuid)
            cleaned = True
    if recipe_no_longer_exists_uuid:
        message = "Recipe no longer exists:\n"
        for _, recipe_path in recipe_no_longer_exists_uuid.items():
            message += f"{recipe_path}\n"
        message += "Clean?"
        response = QtWidgets.QMessageBox.question(
            widget,
            "Inconsistent recipe settings",
            message,
            button0=QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
            button1=QtWidgets.QMessageBox.StandardButton.Yes,
        )
        if response == QtWidgets.QMessageBox.StandardButton.Yes:
            for uuid, _ in recipe_no_longer_exists_uuid.items():
                real_uuid = QtCore.QUuid(uuid)
                RecipeSettingsDeleter().delete(real_uuid)
                RecentRecipeSettingsDeleter().delete(real_uuid)
            cleaned = True
    if recent_recipe_only:
        message = "Missing settings for UUIDs:\n"
        message += "\n".join(recent_recipe_only)
        message += "Clean?"
        response = QtWidgets.QMessageBox.question(
            widget,
            "Inconsistent recipe settings",
            message,
            button0=QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
            button1=QtWidgets.QMessageBox.StandardButton.Yes,
        )
        if response == QtWidgets.QMessageBox.StandardButton.Yes:
            for uuid in recent_recipe_only:
                real_uuid = QtCore.QUuid(uuid)
                RecentRecipeSettingsDeleter().delete(real_uuid)
            cleaned = True
    if all_uuids:
        # all_uuids are now those recipe settings without a recent recipe UUID
        message = "Recent recipe UUIDs that don't have settings:\n"
        message += "\n".join(all_uuids)
        message += "Add?"
        response = QtWidgets.QMessageBox.question(
            widget,
            "Inconsistent recipe settings",
            message,
            button0=QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
            button1=QtWidgets.QMessageBox.StandardButton.Yes,
        )
        if response == QtWidgets.QMessageBox.StandardButton.Yes:
            for uuid in all_uuids:
                real_uuid = QtCore.QUuid(uuid)
                RecentRecipeSettingsWriter().make_current(real_uuid)
            cleaned = True
    return cleaned
