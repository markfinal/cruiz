#!/usr/bin/env python3

"""Wizard pages for naming new Conan local caches."""

import platform
import typing

from PySide6 import QtWidgets

from cruiz.settings.managers.namedlocalcache import AllNamedLocalCacheSettingsReader


class NewLocalCacheNamePage(QtWidgets.QWizardPage):
    """Wizard page method overrides for specifying the new local cache name."""

    def __init__(self, parent: typing.Optional[QtWidgets.QWidget] = None) -> None:
        """Initialise a NewLocalCacheNamePage."""
        super().__init__(parent)
        with AllNamedLocalCacheSettingsReader() as names:
            self._cache_names = names

    def isComplete(self) -> bool:
        """Override whether the page is considered complete."""
        # pylint: disable=protected-access
        text = self.wizard()._ui.new_cache_name.text()  # type: ignore[attr-defined]
        return bool(text) and text not in self._cache_names


class NewLocalCacheLocationPage(QtWidgets.QWizardPage):
    """Wizard page method overrides for specifying the new local cache locations."""

    def isComplete(self) -> bool:
        """Override whether the page is considered complete."""
        # pylint: disable=protected-access
        wizard_user_interface = self.wizard()._ui  # type: ignore[attr-defined]
        if platform.system() == "Windows":
            return bool(wizard_user_interface.userHome.text()) and bool(
                wizard_user_interface.userHomeShort.text()
            )
        return bool(wizard_user_interface.userHome.text())


class NewLocalCacheCreatePage(QtWidgets.QWizardPage):
    """Wizard page method overrides for creating the local cache."""

    def __init__(self, parent: typing.Optional[QtWidgets.QWidget] = None) -> None:
        """Initialise a NewLocalCacheCreatePage."""
        super().__init__(parent)
        self._created = False

    @property
    def created(self) -> bool:
        """Was the local cache created?."""
        return self._created

    @created.setter
    def created(self, value: bool) -> None:
        self._created = value

    def isComplete(self) -> bool:
        """Override whether the page is considered complete."""
        return self.created
