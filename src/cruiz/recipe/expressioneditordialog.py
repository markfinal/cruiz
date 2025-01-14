#!/usr/bin/env python3

"""Local workflow folder expression editor dialog."""

from PySide6 import QtWidgets

from cruiz.pyside6.recipe_local_workflow_expression_editor import (
    Ui_ExpressionEditor,
)


class ExpressionEditorDialog(QtWidgets.QDialog):
    """Dialog for editing expressions for local workflow folders."""

    # parent is RecipeWidget
    def __init__(self, parent: QtWidgets.QWidget) -> None:
        """Initialise an ExpressionEditorDialog."""
        super().__init__(parent)
        self._ui = Ui_ExpressionEditor()
        self._ui.setupUi(self)  # type: ignore[no-untyped-call]

        self._ui.expression.textChanged.connect(self._evaluate)
        tokens, _ = parent.tokens()  # type: ignore[attr-defined]

        self._ui.evaluatedExpression.clear()
        self._ui.nameMacro.setText(tokens["name"])
        self._ui.versionMacro.setText(tokens["version"])
        self._ui.profileMacro.setText(tokens["profile"])
        self._ui.buildtypeMacro.setText(tokens["build_type"])
        self._ui.buildtypelcMacro.setText(tokens["build_type_lc"])

    def _evaluate(self, text: str) -> None:
        try:
            self._ui.evaluatedExpression.setText(self.parent().resolve_expression(text))  # type: ignore[attr-defined] # noqa: E501
        except (ValueError, KeyError):
            self._ui.evaluatedExpression.clear()
