#!/usr/bin/env python3

"""
Wizard for creating new Conan local caches
"""

import platform
import typing

from qtpy import QtGui, QtWidgets, PYSIDE2

from cruiz.commands.context import ConanContext
from cruiz.interop.commandparameters import CommandParameters
from cruiz.commands.logdetails import LogDetails
from cruiz.settings.managers.localcachepreferences import LocalCacheSettingsReader
from cruiz.settings.managers.namedlocalcache import NamedLocalCacheCreator
from cruiz.widgets.util import search_for_dir_options
from cruiz.constants import DEFAULT_CACHE_NAME

import cruiz.workers

if PYSIDE2:
    from cruiz.pyside2.local_cache_new_wizard import Ui_NewLocalCacheWizard

    QAction = QtWidgets.QAction
else:
    from cruiz.pyside6.local_cache_new_wizard import Ui_NewLocalCacheWizard

    QAction = QtGui.QAction


class NewLocalCacheWizard(QtWidgets.QWizard):
    """
    Wizard for creating new local caches
    """

    def __init__(self, parent: typing.Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._ui = Ui_NewLocalCacheWizard()
        self._ui.setupUi(self)  # type: ignore[no-untyped-call]
        self._log_details = LogDetails(self._ui.summary_log, None, True, False, None)
        self._context = ConanContext(DEFAULT_CACHE_NAME, self._log_details)
        self._ui.new_cache_name.textChanged.connect(self._ui.namePage.completeChanged)
        self._ui.userHome.textChanged.connect(self._ui.locationsPage.completeChanged)
        self._ui.userHomeShort.textChanged.connect(
            self._ui.locationsPage.completeChanged
        )
        dir_icon: QtGui.QIcon = self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon)
        browse_home_dir_action = QAction(dir_icon, "", self)
        browse_home_dir_action.triggered.connect(self._browse_for_home_dir)
        self._ui.userHome.addAction(
            browse_home_dir_action,
            QtWidgets.QLineEdit.TrailingPosition,
        )
        browse_short_home_dir_action = QAction(dir_icon, "", self)
        browse_short_home_dir_action.triggered.connect(self._browse_for_short_home_dir)
        self._ui.userHomeShort.addAction(
            browse_short_home_dir_action,
            QtWidgets.QLineEdit.TrailingPosition,
        )
        with LocalCacheSettingsReader() as settings:
            new_config_url = settings.new_configuration_install.resolve()
            new_config_branch = settings.new_configuration_git_branch.resolve()
        self._ui.configUrl.setText(new_config_url)
        self._ui.configBranch.setText(new_config_branch or "<default branch>")
        self._ui.queryConfigInstall.setChecked(bool(new_config_url))
        self._ui.queryConfigInstall.setEnabled(bool(new_config_url))
        self._ui.createCache.clicked.connect(self._create_cache)
        self._ui.createProgress.setMinimum(0)
        self._ui.createProgress.setMaximum(1)
        self._ui.createProgress.setValue(0)
        if platform.system() == "Windows":
            pass
        else:
            self._ui.userHomeShortExplanation.hide()
            self._ui.userHomeShortLabel.hide()
            self._ui.userHomeShort.hide()
        self.currentIdChanged.connect(self._changed_page)

    def done(self, result: int) -> None:
        self._context.close()
        super().done(result)

    def _changed_page(self, page_id: int) -> None:
        if page_id == 4:
            # summary page
            self._ui.summary_name.setText(self._ui.new_cache_name.text())
            self._ui.summary_user_home.setText(self._ui.userHome.text())
            if self._ui.userHomeShort.text():
                self._ui.summary_user_home_short.setText(self._ui.userHomeShort.text())
            else:
                self._ui.summary_user_home_short.hide()
            if self._ui.queryConfigInstall.isChecked():
                if self._ui.configBranch.text():
                    self._ui.summary_install_config.setText(
                        "User chose to install the configuration "
                        f"{self._ui.configUrl.text()} "
                        f"using branch {self._ui.configBranch.text()}"
                    )
                else:
                    self._ui.summary_install_config.setText(
                        "User chose to install the configuration "
                        f"{self._ui.configUrl.text()} "
                        "using the default branch"
                    )
            else:
                self._ui.summary_install_config.setText(
                    "User chose not to install a configuration at this time"
                )

    def _browse_for_home_dir(self) -> None:
        dir_found = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select home directory",
            "",
            search_for_dir_options(),
        )
        if dir_found:
            self._ui.userHome.setText(dir_found)

    def _browse_for_short_home_dir(self) -> None:
        dir_found = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select short home directory",
            "",
            search_for_dir_options(),
        )
        if dir_found:
            self._ui.userHomeShort.setText(dir_found)

    def _create_cache(self) -> None:
        self._ui.createProgress.setMaximum(0)
        name = self._ui.new_cache_name.text().strip()
        NamedLocalCacheCreator().create(
            name,
            self._ui.userHome.text().strip(),
            self._ui.userHomeShort.text().strip(),
        )

        if self._ui.queryConfigInstall.isChecked():
            with LocalCacheSettingsReader() as settings:
                config_install = settings.new_configuration_install.resolve()
                git_branch = settings.new_configuration_git_branch.resolve()
            if config_install:
                self._context.change_cache(name)
                params = CommandParameters(
                    "install_config", cruiz.workers.configinstall.invoke
                )
                named_args = params.named_arguments
                named_args["pathOrUrl"] = config_install
                if git_branch:
                    named_args["gitBranch"] = git_branch
                self._context.install_config(
                    params, self._perform_new_cache_config_install_complete
                )
        self._ui.createProgress.setMaximum(1)
        self._ui.createPage.created = True
        self._ui.createPage.completeChanged.emit()

    def _perform_new_cache_config_install_complete(
        self, result: typing.Any, exception: typing.Any
    ) -> None:
        # pylint: disable=unused-argument
        if exception:
            QtWidgets.QMessageBox.critical(
                self,
                "New local cache configuration install failure",
                str(exception),
            )

    @property
    def switch_to_new_cache(self) -> bool:
        """
        Should the user switch to the new cache once complete?
        """
        return self._ui.summary_switch_to_new.isChecked()

    @property
    def cache_name(self) -> str:
        """
        The name of the new cache once complete
        """
        return self._ui.new_cache_name.text()
