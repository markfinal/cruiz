#!/usr/bin/env python3

"""
Representation of a recipe
"""

import pathlib
import typing

from qtpy import QtCore

from cruiz.commands.context import ConanContext
from cruiz.commands.logdetails import LogDetails


# TODO: need to remember why this is derived from QObject?
# TODO: possibly due to the parent-child ownership, and thus lifetime
class Recipe(QtCore.QObject):
    """
    Sufficient information to uniquely identify a recipe
    """

    def __init__(
        self,
        path: pathlib.Path,
        uuid: QtCore.QUuid,
        cache_name: str,
        log_details: LogDetails,
        parent: QtCore.QObject,
    ) -> None:
        super().__init__(parent)
        self.path = path
        self.uuid = uuid
        self.context = ConanContext(cache_name, log_details)

    def close(self) -> None:
        """
        Close the recipe
        """
        self.context.close()

    @property
    def version(self) -> typing.Optional[str]:
        """
        Get the version of the recipe.
        May be None.
        """
        from cruiz.settings.managers.recipe import RecipeSettingsReader

        with RecipeSettingsReader.from_uuid(self.uuid) as settings:
            attributes = settings.attribute_overrides.resolve()
        return attributes.get("version")

    @property
    def user(self) -> typing.Optional[str]:
        """
        Get the user namespace of the recipe.
        May be None.
        """
        from cruiz.settings.managers.recipe import RecipeSettingsReader

        with RecipeSettingsReader.from_uuid(self.uuid) as settings:
            attributes = settings.attribute_overrides.resolve()
        return attributes.get("user")

    @property
    def channel(self) -> typing.Optional[str]:
        """
        Get the channel namespace of the recipe.
        May be None.
        """
        from cruiz.settings.managers.recipe import RecipeSettingsReader

        with RecipeSettingsReader.from_uuid(self.uuid) as settings:
            attributes = settings.attribute_overrides.resolve()
        return attributes.get("channel")

    @property
    def folder(self) -> pathlib.Path:
        """
        Get the folder containing the recipe.
        """
        return self.path.parent
