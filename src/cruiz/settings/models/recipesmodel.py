#!/usr/bin/env python3

"""Qt model for recipes."""

import typing

from PySide6 import QtCore

import cruiz.globals
from cruiz.settings.managers.recipe import RecipeSettingsReader


class RecipesModel(QtCore.QAbstractTableModel):
    """Model representing a Conan recipe."""

    def __init__(self) -> None:
        """Initialise a RecipesModel."""
        super().__init__()
        self._uuids: typing.Optional[typing.List[QtCore.QUuid]] = None

    def set_uuids(self, uuids: typing.List[QtCore.QUuid]) -> None:
        """Set the recipe UUIDs for the model."""
        self.beginResetModel()
        self._uuids = uuids
        self.endResetModel()

    def uuid(self, index: int) -> QtCore.QUuid:
        """Get the recipe UUID specified by its index."""
        assert self._uuids
        return self._uuids[index]

    def rowCount(self, parent) -> int:  # type: ignore
        """Get the row count of the model."""
        if parent.isValid():
            return 0
        if self._uuids is None:
            return 0
        return len(self._uuids)

    def columnCount(self, parent) -> int:  # type: ignore
        """Get the column count of the model."""
        # pylint: disable=unused-argument
        return 3

    def headerData(self, section, orientation, role):  # type: ignore
        """Get the header data of the model."""
        if (
            role == QtCore.Qt.ItemDataRole.DisplayRole
            and orientation == QtCore.Qt.Orientation.Horizontal
        ):
            if not section:
                return "Path"
            if section == 1:
                return "Version"
            if section == 2:
                return "Local cache"
        return None

    def data(self, index, role):  # type: ignore
        """Get data from the model."""
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            assert self._uuids
            if not index.column():
                with RecipeSettingsReader.from_uuid(
                    self._uuids[index.row()]
                ) as settings:
                    return settings.path.resolve()
            if index.column() == 1:
                with RecipeSettingsReader.from_uuid(
                    self._uuids[index.row()]
                ) as settings:
                    attributes = settings.attribute_overrides.resolve()
                if "version" in attributes:
                    return attributes["version"]
            if index.column() == 2:
                with RecipeSettingsReader.from_uuid(
                    self._uuids[index.row()]
                ) as settings:
                    return settings.local_cache_name.resolve()
        return None

    def flags(self, index):  # type: ignore
        """Get flags of the cells in the model."""
        def_flags = super().flags(index)
        if self._uuids and cruiz.globals.get_main_window().is_recipe_active(
            self._uuids[index.row()]
        ):
            return def_flags & ~QtCore.Qt.ItemFlag.ItemIsEnabled
        return def_flags
