#!/usr/bin/env python3

"""
Wizard page for selecting a local cache
"""

import typing

from qtpy import QtWidgets

from cruiz.widgets.util import BlockSignals
from cruiz.settings.managers.namedlocalcache import AllNamedLocalCacheSettingsReader
from cruiz.settings.managers.recipe import RecipeSettingsReader
from cruiz.manage_local_cache import ManageLocalCachesDialog


class LoadRecipeLocalCachePage(QtWidgets.QWizardPage):
    """
    Wizard page for selecting the local cache to associate with the recipe instance.
    """

    @property
    def _ui(self) -> typing.Any:
        return self.wizard().ui

    def nextId(self) -> int:
        return 3

    def initializePage(self) -> None:
        self.registerField("local_cache*", self._ui.local_cache_name, "currentText")
        self._ui.local_cache_name.currentIndexChanged.connect(
            self._on_local_cache_changed
        )
        self._ui.manage_caches.clicked.connect(self._on_manage_caches)
        self._populate_caches()
        if self.wizard().original_recipe:
            with RecipeSettingsReader.from_recipe(
                self.wizard().original_recipe
            ) as settings:
                original_cache = settings.local_cache_name.resolve()
            self._ui.local_cache_name.setCurrentText(original_cache)
        super().initializePage()

    def cleanupPage(self) -> None:
        self._ui.local_cache_name.currentIndexChanged.disconnect()
        return super().cleanupPage()

    def _populate_caches(self) -> None:
        with BlockSignals(self._ui.local_cache_name) as blocked_widget:
            blocked_widget.clear()
            with AllNamedLocalCacheSettingsReader() as names:
                blocked_widget.addItems(names)
            blocked_widget.setCurrentIndex(-1)

    def _on_local_cache_changed(self, index: int) -> None:
        # pylint: disable=unused-argument
        self.completeChanged.emit()

    def _on_manage_caches(self) -> None:
        ManageLocalCachesDialog(self, None).exec_()
        self._populate_caches()
