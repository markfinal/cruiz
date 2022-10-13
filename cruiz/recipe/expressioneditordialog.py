#!/usr/bin/env python3

"""
Local workflow folder expression editor dialog
"""

from qtpy import QtWidgets, PYSIDE2

if PYSIDE2:
    from cruiz.pyside2.recipe_local_workflow_expression_editor import (
        Ui_ExpressionEditor,
    )
else:
    from cruiz.pyside6.recipe_local_workflow_expression_editor import (
        Ui_ExpressionEditor,
    )


class ExpressionEditorDialog(QtWidgets.QDialog):
    """
    Dialog for editing expressions for local workflow folders
    """

    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)
        self._ui = Ui_ExpressionEditor()
        self._ui.setupUi(self)  # type: ignore[no-untyped-call]

        self._ui.expression.textChanged.connect(self._evaluate)
        tokens, _ = parent.tokens()

        self._ui.evaluatedExpression.clear()
        self._ui.nameMacro.setText(tokens["name"])
        self._ui.versionMacro.setText(tokens["version"])
        self._ui.profileMacro.setText(tokens["profile"])
        self._ui.buildtypeMacro.setText(tokens["build_type"])
        self._ui.buildtypelcMacro.setText(tokens["build_type_lc"])

    def _evaluate(self, text: str) -> None:
        try:
            self._ui.evaluatedExpression.setText(self.parent().resolve_expression(text))
        except (ValueError, KeyError):
            self._ui.evaluatedExpression.clear()
