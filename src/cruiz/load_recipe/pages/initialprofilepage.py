#!/usr/bin/env python3

"""
Wizard page for selecting the initial profile
"""

import pathlib
import typing

from qtpy import QtWidgets

from cruiz.commands.context import managed_conan_context
from cruiz.commands.logdetails import LogDetails

from cruiz.widgets.util import BlockSignals
from cruiz.settings.managers.recipe import RecipeSettingsReader


class LoadRecipeInitialProfilePage(QtWidgets.QWizardPage):
    """
    Wizard page allowing selection of an initial profile to apply to the recipe.
    """

    @property
    def _ui(self) -> typing.Any:
        return self.wizard().ui

    def nextId(self) -> int:
        return -1

    def initializePage(self) -> None:
        self.registerField(
            "initial_profile*", self._ui.initial_profile, "currentText"  # type: ignore
        )
        self._ui.initial_profile.currentIndexChanged.connect(
            self._on_initial_profile_changed
        )
        with BlockSignals(self._ui.initial_profile) as blocked_widget:
            blocked_widget.clear()
            for profile_path in self._get_profile_list():
                blocked_widget.addItem(str(profile_path))
            blocked_widget.setCurrentIndex(-1)
        if self.wizard().original_recipe:
            with RecipeSettingsReader.from_recipe(
                self.wizard().original_recipe
            ) as settings:
                original_profile = settings.profile.resolve()
            self._ui.initial_profile.setCurrentText(original_profile)
        super().initializePage()

    def cleanupPage(self) -> None:
        self._ui.initial_profile.currentIndexChanged.disconnect()
        return super().cleanupPage()

    def _on_initial_profile_changed(self, index: int) -> None:
        # pylint: disable=unused-argument
        self.completeChanged.emit()

    def _get_profile_list(self) -> typing.List[pathlib.Path]:
        self._ui.initial_profile_log.hide()
        log_details = LogDetails(self._ui.initial_profile_log, None, True, False, None)
        log_details.logging.connect(self._on_get_profile_list_output)
        with managed_conan_context(
            self._ui.local_cache_name.currentText(), log_details
        ) as context:
            profile_list = context.get_list_of_profiles()
        return [p[0] for p in profile_list]

    def _on_get_profile_list_output(self) -> None:
        self._ui.initial_profile_log.show()
