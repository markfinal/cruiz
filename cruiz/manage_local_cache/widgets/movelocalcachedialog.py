#!/usr/bin/env python3

"""
Dialog for moving local caches
"""

import pathlib
import platform
import shutil
import typing

from qtpy import QtCore, QtGui, QtWidgets

import cruiz.globals

from cruiz.commands.context import ConanContext

from cruiz.settings.managers.namedlocalcache import (
    NamedLocalCacheSettings,
    NamedLocalCacheSettingsReader,
    NamedLocalCacheSettingsWriter,
)

from cruiz.pyside6.local_cache_move import Ui_LocalCacheMove

from cruiz.widgets.util import search_for_dir_options


class MoveLocalCacheDialog(QtWidgets.QDialog):
    """
    Dialog for moving a non-default local cache.
    """

    def __init__(self, context: ConanContext, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self._context = context
        self._ui = Ui_LocalCacheMove()
        self._ui.setupUi(self)  # type: ignore[no-untyped-call]
        with NamedLocalCacheSettingsReader(context.cache_name) as settings:
            self._ui.currentUserHome.setText(settings.home_dir.resolve())
            self._ui.currentUserHomeShort.setText(settings.short_home_dir.resolve())
        self._ui.buttonBox.accepted.connect(self.accept)
        self._ui.buttonBox.rejected.connect(self.reject)
        home_dir_browse_action = QtGui.QAction(
            self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon), "", self
        )
        home_dir_browse_action.triggered.connect(self._home_dir_browse)
        self._ui.newUserHome.addAction(
            home_dir_browse_action,
            QtWidgets.QLineEdit.TrailingPosition,
        )
        self._ui.newUserHome.textChanged.connect(self._new_path_changed)
        self._ui.newUserHomeShort.textChanged.connect(self._new_path_changed)
        self._ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        if cruiz.globals.CONAN_MAJOR_VERSION == 1:
            if platform.system() == "Windows":
                pass
            else:
                self._ui.userHomeShortLabel.hide()
                self._ui.currentUserHomeShort.hide()
                self._ui.newUserHomeShort.hide()
        else:
            self._ui.userHomeShortLabel.hide()
            self._ui.currentUserHomeShort.hide()
            self._ui.newUserHomeShort.hide()

    def _home_dir_browse(self) -> None:
        dir_found = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select home directory to move to",
            self._ui.currentUserHome.text(),
            search_for_dir_options(),
        )
        if dir_found:
            self._ui.newUserHome.setText(dir_found)

    def _new_path_changed(self, path: str) -> None:
        # pylint: disable=unused-argument
        if platform.system() == "Windows":
            condition = bool(self._ui.newUserHome.text()) and bool(
                self._ui.newUserHomeShort.text()
            )
        else:
            condition = bool(self._ui.newUserHome.text()) or bool(
                self._ui.newUserHomeShort.text()
            )
        self._ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(condition)

    def accept(self) -> None:
        with NamedLocalCacheSettingsReader(self._context.cache_name) as settings:
            home_dir = settings.home_dir.resolve()
            short_home_dir = settings.short_home_dir.resolve()
        new_home_dir = self._ui.newUserHome.text().strip()
        if new_home_dir == home_dir:
            QtWidgets.QMessageBox.critical(
                self,
                "Conan local cache home directory",
                f"The selected home directory '{new_home_dir}' is unchanged. "
                "Please choose another.",
            )
            return
        qdir = QtCore.QDir(new_home_dir)
        if cruiz.globals.CONAN_MAJOR_VERSION == 1 and qdir.exists():
            QtWidgets.QMessageBox.critical(
                self,
                "Conan local cache home directory",
                f"The selected home directory '{new_home_dir}' already exists. "
                "Please choose another.",
            )
            return
        if not qdir.isEmpty():
            QtWidgets.QMessageBox.critical(
                self,
                "Conan local cache home directory",
                f"The selected home directory '{new_home_dir}' is not empty. "
                "Please choose another.",
            )
            return
        if short_home_dir:
            new_short_home_dir = self._ui.newUserHomeShort.text().strip()
            if new_short_home_dir == short_home_dir:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Conan local cache short home directory",
                    f"The selected short home directory '{new_short_home_dir}' "
                    "is unchanged. Please choose another.",
                )
                return
            qdir = QtCore.QDir(new_short_home_dir)
            if qdir.exists():
                QtWidgets.QMessageBox.critical(
                    self,
                    "Conan local cache short home directory",
                    f"The selected short home directory '{new_short_home_dir}' already"
                    " exists. Please choose another.",
                )
                return
            if not qdir.isEmpty():
                QtWidgets.QMessageBox.critical(
                    self,
                    "Conan local cache short home directory",
                    f"The selected short home directory '{new_short_home_dir}' is "
                    "not empty. Please choose another.",
                )
                return
        else:
            new_short_home_dir = None
        self._move(settings, home_dir, short_home_dir, new_home_dir, new_short_home_dir)
        super().accept()

    def _move(
        self,
        settings: NamedLocalCacheSettings,
        old_home_dir: str,
        old_short_home_dir: str,
        new_home_dir: str,
        new_short_home_dir: typing.Optional[str],
    ) -> None:
        assert old_home_dir  # since it's non-default
        # update settings
        settings.home_dir = new_home_dir  # type: ignore
        settings.short_home_dir = new_short_home_dir  # type: ignore
        NamedLocalCacheSettingsWriter(self._context.cache_name).sync(settings)
        # pylint: disable=broad-except
        try:
            old_conan_dir = pathlib.Path(old_home_dir)
            new_conan_dir = pathlib.Path(new_home_dir)
            if cruiz.globals.CONAN_MAJOR_VERSION == 1:
                # move <old>/.conan to <new>/.conan
                old_conan_dir /= ".conan"
                new_conan_dir /= ".conan"
            shutil.move(str(old_conan_dir), str(new_conan_dir))
        except Exception as exception:
            QtWidgets.QMessageBox.critical(
                self,
                "Conan move local cache",
                f"Failed to move the local cache home dir because: {exception}.",
            )
            # roll back previous steps
            settings.home_dir = old_home_dir  # type: ignore
            settings.short_home_dir = old_short_home_dir  # type: ignore
            NamedLocalCacheSettingsWriter(self._context.cache_name).sync(settings)
            return
        else:
            if old_short_home_dir:
                try:
                    assert new_short_home_dir
                    shutil.move(old_short_home_dir, new_short_home_dir)
                except Exception as exception:
                    QtWidgets.QMessageBox.critical(
                        self,
                        "Conan move local cache",
                        "Failed to move the local cache short home dir because: "
                        f"{exception}.",
                    )
                    # roll back previous steps
                    shutil.move(new_home_dir, str(old_conan_dir))
                    settings.home_dir = old_home_dir  # type: ignore
                    settings.short_home_dir = old_short_home_dir  # type: ignore
                    NamedLocalCacheSettingsWriter(self._context.cache_name).sync(
                        settings
                    )
                    return
        if cruiz.globals.CONAN_MAJOR_VERSION == 1:
            qdir = QtCore.QDir(old_home_dir)
            if qdir.isEmpty():
                qdir.removeRecursively()
