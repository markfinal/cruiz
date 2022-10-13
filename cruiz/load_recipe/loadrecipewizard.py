#!/usr/bin/env python3

"""
Wizard for loading a recipe
"""

import pathlib
import typing

from qtpy import QtCore, QtWidgets, PYSIDE2

if PYSIDE2:
    from cruiz.pyside2.load_recipe_wizard import Ui_LoadRecipeWizard
else:
    from cruiz.pyside6.load_recipe_wizard import Ui_LoadRecipeWizard

from cruiz.exceptions import RecipeDoesNotExistError, RecipeAlreadyOpenError
from cruiz.settings.managers.recipe import RecipeSettings, RecipeSettingsReader
from cruiz.recipe.recipewidget import Recipe

from cruiz.commands.context import managed_conan_context
from cruiz.commands.logdetails import LogDetails
from cruiz.constants import DEFAULT_CACHE_NAME

import cruiz.globals


class LoadRecipeWizard(QtWidgets.QWizard):
    """
    Wizard for loading recipes.
    """

    def __init__(
        self,
        parent: QtWidgets.QWidget,
        path: pathlib.Path,
        uuid: typing.Optional[QtCore.QUuid],
        original_recipe: typing.Optional[Recipe],
    ) -> None:
        super().__init__(parent)
        self.has_load_errors = False
        self._path = path
        self._uuid = uuid
        self.original_recipe = original_recipe
        self._ambiguous_version = False
        self.validate()
        if self._uuid:
            # likely to have come via the recent recipe menu
            with RecipeSettingsReader.from_uuid(self._uuid) as settings:
                self._existing_cache_name = settings.local_cache_name.resolve()
            assert self._existing_cache_name is not None
        else:
            self.matching_uuids = RecipeSettings().matching_uuids(self._path)
            if self.matching_uuids:
                if len(self.matching_uuids) == 1:
                    recipe_uuid = self.matching_uuids[0]
                    with RecipeSettingsReader.from_uuid(recipe_uuid) as settings:
                        package_attributes = settings.attribute_overrides.resolve()
                    if "version" in package_attributes:
                        # a version has been been used as an override
                        self._ambiguous_version = True
                else:
                    self._ambiguous_version = True
        self.ui = Ui_LoadRecipeWizard()
        self.ui.setupUi(self)  # type: ignore[no-untyped-call]

        if self.disambiguation_required:
            self.ui.intro_message.hide()
            log_details = LogDetails(self.ui.intro_message, None, True, False, None)
            log_details.logging.connect(self._on_error_loading)
            with managed_conan_context(DEFAULT_CACHE_NAME, log_details) as context:
                self.recipe_attributes = context.inspect_recipe(self._path)
                self.conandata = context.get_conandata(self._path)

    def _on_error_loading(self) -> None:
        self.ui.intro_message.show()
        self.has_load_errors = True

    @property
    def disambiguation_required(self) -> bool:
        """
        Determine whether the recipe needs to be disambiguated by user input.
        """
        return self._uuid is None or self._ambiguous_version

    @property
    def recipe_version(self) -> typing.Optional[str]:
        """
        Get the version of the recipe. May be None.
        """
        if self.ui.version.isEnabled():
            return self.field("version")
        return None

    @property
    def local_cache(self) -> str:
        """
        Get the local cache to use, either from a clone of an existing recipe
        or from user selection.
        """
        if self._uuid:
            # come via the recent recipe menu, or chosen as a version
            # from 'open another version'
            with RecipeSettingsReader.from_uuid(self._uuid) as settings:
                existing_cache_name = settings.local_cache_name.resolve()
            assert existing_cache_name is not None
            return existing_cache_name
        return self.field("local_cache")

    @property
    def initial_profile(self) -> str:
        """
        Get the initial profile selected.
        """
        return self.field("initial_profile")

    @property
    def uuid(self) -> typing.Optional[QtCore.QUuid]:
        """
        Get the uuid to use for the recipe.
        May be None to indicate that the recipe has not been seen before.
        """
        return self._uuid

    @uuid.setter
    def uuid(self, uuid: typing.Optional[QtCore.QUuid]) -> None:
        """
        Allow setting the uuid. May be None.
        """
        self._uuid = uuid

    def validate(self) -> None:
        """
        Validate the recipe in the wizard.
        """
        if not self._path.exists():
            raise RecipeDoesNotExistError()
        if self._uuid:
            if cruiz.globals.get_main_window().is_recipe_active(self._uuid):
                raise RecipeAlreadyOpenError()
