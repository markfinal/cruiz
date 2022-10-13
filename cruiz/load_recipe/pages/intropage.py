#!/usr/bin/env python3

"""
Wizard introduction page
"""

from qtpy import QtWidgets


class LoadRecipeIntroPage(QtWidgets.QWizardPage):
    """
    Wizard page serving as an introduction to loading recipes.
    """

    def nextId(self) -> int:
        return -1 if self.wizard().has_load_errors else 1
