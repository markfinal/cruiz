#!/usr/bin/env python3

"""
Recipe behaviour toolbar
"""

import os
import pathlib

from qtpy import QtCore, QtWidgets

import cruiz.globals

from cruiz.pyside6.recipe_profile_frame import Ui_profileFrame
from cruiz.pyside6.recipe_cpucores_frame import Ui_cpuCoresFrame

from cruiz.widgets.util import BlockSignals

from cruiz.settings.managers.recipe import (
    RecipeSettings,
    RecipeSettingsReader,
    RecipeSettingsWriter,
)
from cruiz.settings.managers.namedlocalcache import NamedLocalCacheSettingsReader

from cruiz.recipe.recipe import Recipe


class _ProfileFrame(QtWidgets.QFrame):
    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)
        self._ui = Ui_profileFrame()
        self._ui.setupUi(self)  # type: ignore[no-untyped-call]
        self._ui.profileCombo.currentTextChanged.connect(self._changed_profile)

    @property
    def _recipe(self) -> Recipe:
        toolbar = self.parent()
        recipe_widget = toolbar.parent()
        recipe = recipe_widget.recipe
        return recipe

    def _refresh_tooltip(self) -> None:
        cache_name = self._recipe.context.cache_name
        with NamedLocalCacheSettingsReader(cache_name) as settings:
            home_dir = settings.home_dir.resolve()
        # using normcase for Windows path compares
        home_dir = os.path.normcase(home_dir) if home_dir else str(pathlib.Path.home())
        profile_dirs = "\n  ".join(
            [str(os.path.normcase(p)) for p in self._recipe.context.all_profile_dirs()]
        )
        local_cache_envvar = (
            "<CONAN_USER_HOME>"
            if cruiz.globals.CONAN_MAJOR_VERSION == 1
            else "<CONAN_HOME>"
        )
        parameterised_profile_dirs = profile_dirs.replace(home_dir, local_cache_envvar)
        tooltip = (
            "Profiles listed here are from the following directories:\n\n"
            f"{profile_dirs}\n\n"
            "which can be read as this parameterisation\n\n"
            f"{parameterised_profile_dirs}\n\n"
            f"where {local_cache_envvar} is the base directory "
            "for this recipe's associated local cache, called "
            f"'{cache_name}'"
        )
        self._ui.profileCombo.setToolTip(tooltip)
        self._ui.profileLabel.setToolTip(tooltip)

    def refresh_content(self, recipe: Recipe) -> None:
        """
        Refresh the contents.
        """
        profile_list = recipe.context.get_list_of_profiles()
        with RecipeSettingsReader.from_recipe(recipe) as settings:
            current_profile = settings.profile.resolve()
        with BlockSignals(self._ui.profileCombo) as blocked_widget:
            blocked_widget.clear()
            for profile_path, _ in profile_list:
                blocked_widget.addItem(str(profile_path))

            index = blocked_widget.findText(current_profile)
            if index >= 0:
                blocked_widget.setCurrentIndex(index)
            else:
                if profile_list:
                    # this means that the profile in settings cannot be found in the
                    # local cache profiles
                    blocked_widget.setCurrentIndex(0)
                    # sync that the first profile in the list is now current
                    updated_profile_settings = RecipeSettings()
                    updated_profile_settings.profile = str(
                        profile_list[0][0]
                    )  # type: ignore
                    RecipeSettingsWriter().from_recipe(recipe).sync(
                        updated_profile_settings
                    )
                else:
                    blocked_widget.setCurrentIndex(-1)
        self._refresh_tooltip()

    def _changed_profile(self, text: str) -> None:
        recipe = self._recipe
        settings = RecipeSettings.from_recipe(recipe)
        settings.profile = text  # type: ignore
        # note: has to be from recipe, as the profile setter needs
        # the ConanContext to check the default profile name
        RecipeSettingsWriter.from_recipe(recipe).sync(settings)
        self.parent().profile_changed.emit(text)


class _CPUCoresFrame(QtWidgets.QFrame):
    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)
        self._ui = Ui_cpuCoresFrame()
        self._ui.setupUi(self)  # type: ignore[no-untyped-call]
        self._ui.cpuCoresSpin.valueChanged.connect(self._changed_num_cores)

    @property
    def _recipe(self) -> Recipe:
        toolbar = self.parent()
        recipe_widget = toolbar.parent()
        recipe = recipe_widget.recipe
        return recipe

    def refresh_content(self, recipe: Recipe) -> None:
        """
        Refresh the contents.
        """
        with RecipeSettingsReader.from_recipe(recipe) as settings:
            num_cores = settings.num_cpu_cores
        if num_cores.value is None:
            self._ui.cpuCoresSpin.setStyleSheet("color: green;")
        elif num_cores.value > num_cores.fallback:
            self._ui.cpuCoresSpin.setStyleSheet("color: orange;")
        elif num_cores.value < num_cores.fallback:
            self._ui.cpuCoresSpin.setStyleSheet("color: red;")
        with BlockSignals(self._ui.cpuCoresSpin) as blocked_widget:
            blocked_widget.setValue(num_cores.resolve())

    def _changed_num_cores(self, value: int) -> None:
        recipe = self._recipe
        settings = RecipeSettings.from_recipe(recipe)
        settings.num_cpu_cores = value  # type: ignore
        RecipeSettingsWriter.from_recipe(recipe).sync(settings)
        self.refresh_content(recipe)


class RecipeBehaviourToolbar(QtWidgets.QToolBar):
    """
    QToolBar representing tne behaviour of a recipe, profile and cpu cores
    CPU cores not available in Conan 2 at this time
    """

    profile_changed = QtCore.Signal(str)

    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)
        self._profile = _ProfileFrame(self)
        self.addWidget(self._profile)
        if cruiz.globals.CONAN_MAJOR_VERSION == 1:
            self._cpu_cores = _CPUCoresFrame(self)
            self.addSeparator()
            self.addWidget(self._cpu_cores)

    @property
    def _recipe(self) -> Recipe:
        recipe_widget = self.parent()
        recipe = recipe_widget.recipe
        return recipe

    def refresh_content(self) -> None:
        """
        Refresh the content of the toolbar.
        """
        recipe = self._recipe
        self._profile.refresh_content(recipe)
        if cruiz.globals.CONAN_MAJOR_VERSION == 1:
            self._cpu_cores.refresh_content(recipe)
