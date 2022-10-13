#!/usr/bin/env python3

"""
Build features toolbar
"""

import typing

from qtpy import QtCore, QtGui, QtWidgets, PYSIDE2

from cruiz.constants import CompilerCacheTypes

from cruiz.settings.managers.recipe import (
    RecipeSettingsReader,
    RecipeSettings,
    RecipeSettingsWriter,
)
from cruiz.settings.managers.compilercachepreferences import CompilerCacheSettingsReader

from cruiz.widgets.util import BlockSignals

if PYSIDE2:
    from cruiz.pyside2.recipe_cmake_features_frame import Ui_cmakeFeaturesFrame
    from cruiz.pyside2.recipe_compilercache_features_frame import (
        Ui_compilerCacheFrame,
    )
    from cruiz.pyside2.recipe_compiler_cache_configuration_dialog import (
        Ui_CompilerCacheConfigurationDialog,
    )
else:
    from cruiz.pyside6.recipe_cmake_features_frame import Ui_cmakeFeaturesFrame
    from cruiz.pyside6.recipe_compilercache_features_frame import (
        Ui_compilerCacheFrame,
    )
    from cruiz.pyside6.recipe_compiler_cache_configuration_dialog import (
        Ui_CompilerCacheConfigurationDialog,
    )


class _CMakeFeaturesFrame(QtWidgets.QFrame):
    def __init__(self, parent: typing.Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._ui = Ui_cmakeFeaturesFrame()
        self._ui.setupUi(self)  # type: ignore[no-untyped-call]
        self._uuid: typing.Optional[QtCore.QUuid] = None
        self._ui.cmakeFindDebug.stateChanged.connect(self._toggle_cmake_find_debug_mode)
        self._ui.cmakeVerbose.stateChanged.connect(self._toggle_cmake_verbose)

    def refresh_content(self, uuid: QtCore.QUuid) -> None:
        """
        Refresh the content of the frame for the specified recipe UUID
        """
        self._uuid = uuid
        with RecipeSettingsReader.from_uuid(uuid) as settings:
            find_debug = settings.cmake_find_debug.resolve()
            verbose = settings.cmake_verbose.resolve()
        with BlockSignals(self._ui.cmakeFindDebug) as blocked_widget:
            blocked_widget.setChecked(find_debug)
        with BlockSignals(self._ui.cmakeVerbose) as blocked_widget:
            blocked_widget.setChecked(verbose)

    def _toggle_cmake_find_debug_mode(self, state: int) -> None:
        is_checked = state == QtCore.Qt.Checked  # type: ignore[comparison-overlap]
        settings = RecipeSettings()
        settings.cmake_find_debug = is_checked  # type: ignore
        assert self._uuid
        RecipeSettingsWriter.from_uuid(self._uuid).sync(settings)

    def _toggle_cmake_verbose(self, state: int) -> None:
        is_checked = state == QtCore.Qt.Checked  # type: ignore[comparison-overlap]
        settings = RecipeSettings()
        settings.cmake_verbose = is_checked  # type: ignore
        assert self._uuid
        RecipeSettingsWriter.from_uuid(self._uuid).sync(settings)


class _CompilerCacheConfigurationDialog(QtWidgets.QDialog):
    modified = QtCore.Signal()

    def __init__(
        self, uuid: QtCore.QUuid, parent: typing.Optional[QtWidgets.QWidget] = None
    ) -> None:
        super().__init__(parent)
        self._ui = Ui_CompilerCacheConfigurationDialog()
        self._ui.setupUi(self)  # type: ignore[no-untyped-call]
        self._uuid = uuid
        self._settings = RecipeSettings.from_uuid(uuid)
        # -- signals
        self.modified.connect(self._modification_applied)
        self._ui.buttonBox.button(
            QtWidgets.QDialogButtonBox.StandardButton.Apply
        ).setEnabled(False)
        self._ui.buttonBox.button(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
        ).setEnabled(False)
        self._ui.buttonBox.button(
            QtWidgets.QDialogButtonBox.StandardButton.Apply
        ).clicked.connect(self._save)
        self._ui.buttonBox.button(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
        ).clicked.connect(self._save)
        self._ui.buttonBox.button(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
        ).clicked.connect(self.accept)
        self._ui.ccache_arguments.textChanged.connect(self._change_ccache_arguments)
        self._ui.sccache_arguments.textChanged.connect(self._change_sccache_arguments)
        self._ui.buildcache_arguments.textChanged.connect(
            self._change_buildcache_arguments
        )
        self._load_defaults()

    def _load_defaults(self) -> None:
        with RecipeSettingsReader.from_uuid(self._uuid) as settings:
            args = settings.compilercache_autotools_configuration.resolve()
        if CompilerCacheTypes.CCACHE.name in args:
            with BlockSignals(self._ui.ccache_arguments) as blocked_widget:
                blocked_widget.setText(args[CompilerCacheTypes.CCACHE.name])
        if CompilerCacheTypes.SCCACHE.name in args:
            with BlockSignals(self._ui.sccache_arguments) as blocked_widget:
                blocked_widget.setText(args[CompilerCacheTypes.SCCACHE.name])
        if CompilerCacheTypes.BUILDCACHE.name in args:
            with BlockSignals(self._ui.buildcache_arguments) as blocked_widget:
                blocked_widget.setText(args[CompilerCacheTypes.BUILDCACHE.name])

    def _any_modifications(self) -> bool:
        return not self._settings.empty(RecipeSettingsReader.from_uuid(self._uuid))

    def _modification_applied(self) -> None:
        enabled = self._any_modifications()
        self._ui.buttonBox.button(
            QtWidgets.QDialogButtonBox.StandardButton.Apply
        ).setEnabled(enabled)
        self._ui.buttonBox.button(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
        ).setEnabled(enabled)

    def _save(self) -> None:
        RecipeSettingsWriter.from_uuid(self._uuid).sync(self._settings)
        self.modified.emit()

    def reject(self) -> None:
        if self._any_modifications():
            response = QtWidgets.QMessageBox.question(
                self,
                "Unsaved compiler cache arguments",
                "Modifications are unsaved. Do you want to discard them?",
            )
            if response == QtWidgets.QMessageBox.No:
                return
        super().reject()

    def _change_ccache_arguments(self, text: str) -> None:
        self._settings.append_compilercache_autotools_configuration(
            CompilerCacheTypes.CCACHE, text or None
        )
        self.modified.emit()

    def _change_sccache_arguments(self, text: str) -> None:
        self._settings.append_compilercache_autotools_configuration(
            CompilerCacheTypes.SCCACHE, text or None
        )
        self.modified.emit()

    def _change_buildcache_arguments(self, text: str) -> None:
        self._settings.append_compilercache_autotools_configuration(
            CompilerCacheTypes.BUILDCACHE, text or None
        )
        self.modified.emit()


class _CompilerCacheFeaturesFrame(QtWidgets.QFrame):
    def __init__(self, parent: typing.Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._ui = Ui_compilerCacheFrame()
        self._ui.setupUi(self)  # type: ignore[no-untyped-call]
        self._uuid: typing.Optional[QtCore.QUuid] = None
        self._ui.useCache.stateChanged.connect(self._toggle_use_cache)
        self._ui.chooseCache.currentTextChanged.connect(self._change_cache)
        self._ui.configureCache.clicked.connect(self._open_configuration)

    def refresh_content(self, uuid: QtCore.QUuid) -> None:
        """
        Refresh the content of the frame for the specified recipe UUID
        """
        self._uuid = uuid
        with RecipeSettingsReader.from_uuid(uuid) as settings:
            compiler_cache = settings.compiler_cache.resolve()
        with BlockSignals(self._ui.useCache) as blocked_widget:
            blocked_widget.setChecked(bool(compiler_cache))
        with BlockSignals(self._ui.chooseCache) as blocked_widget:
            blocked_widget.setEnabled(bool(compiler_cache))
            default_compiler_cache = self._identify_default_compiler_cache()
            blocked_widget.setCurrentText(compiler_cache or default_compiler_cache)

    def _identify_default_compiler_cache(self) -> str:
        with CompilerCacheSettingsReader() as settings:
            default_compiler_cache = settings.default.resolve()
        default_index = self._ui.chooseCache.findText(default_compiler_cache)
        assert default_index >= 0
        for i in range(self._ui.chooseCache.count()):
            self._ui.chooseCache.setItemIcon(
                i,
                QtGui.QIcon(":/cruiz.png") if i == default_index else QtGui.QIcon(),
            )
        return default_compiler_cache

    def _toggle_use_cache(self, state: int) -> None:
        is_checked = state == QtCore.Qt.Checked  # type: ignore[comparison-overlap]
        settings = RecipeSettings()
        cache_name = self._ui.chooseCache.currentText() if is_checked else None
        settings.compiler_cache = cache_name  # type: ignore[assignment]
        assert self._uuid
        RecipeSettingsWriter.from_uuid(self._uuid).sync(settings)
        self._ui.chooseCache.setEnabled(is_checked)
        self.refresh_content(self._uuid)

    def _change_cache(self, text: str) -> None:
        settings = RecipeSettings()
        settings.compiler_cache = text  # type: ignore
        assert self._uuid
        RecipeSettingsWriter.from_uuid(self._uuid).sync(settings)

    def _open_configuration(self) -> None:
        assert self._uuid
        _CompilerCacheConfigurationDialog(self._uuid, self).exec_()


class BuildFeaturesToolbar(QtWidgets.QToolBar):
    """
    QToolBar representing the build features of a recipe, CMake and compiler caching
    """

    def __init__(self, parent: typing.Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._cmake_features = _CMakeFeaturesFrame()
        self._compilercache_features = _CompilerCacheFeaturesFrame()
        self.addWidget(self._cmake_features)
        self.addSeparator()
        self.addWidget(self._compilercache_features)
        self.addSeparator()

    def refresh_content(self, uuid: QtCore.QUuid) -> None:
        """
        Refresh the content of the toolbar.
        """
        self._cmake_features.refresh_content(uuid)
        self._compilercache_features.refresh_content(uuid)
