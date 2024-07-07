#!/usr/bin/env python3

"""
Wizard page for selecting the version of the package
"""

import typing

from qtpy import QtGui, QtWidgets

from cruiz.widgets.util import BlockSignals
from cruiz.settings.managers.conanpreferences import ConanSettingsReader
from cruiz.settings.managers.recipe import RecipeSettingsReader

import cruiz.globals


class LoadRecipePackageVersionPage(QtWidgets.QWizardPage):
    """
    Wizard page for selecting the recipe version to bind to.
    """

    @property
    def _ui(self) -> typing.Any:
        return self.wizard().ui

    def nextId(self) -> int:
        if self._ui.version.currentText() in self._uuid_versions:
            return -1
        return 2

    def initializePage(self) -> None:
        self.registerField("version*", self._ui.version, "currentText")

        self._ui.version.currentTextChanged.connect(self._on_version_changed)

        self._uuid_versions: typing.Dict[str, str] = {}
        self._resolve_ui_to_possible_versions()
        super().initializePage()

    def cleanupPage(self) -> None:
        self._ui.version.currentTextChanged.disconnect()
        return super().cleanupPage()

    def _on_version_changed(self, text: str) -> None:
        if text in self._uuid_versions:
            self.setFinalPage(True)
            self.wizard().uuid = self._uuid_versions[text]
        else:
            self.wizard().uuid = None
        self.completeChanged.emit()

    def _resolve_ui_to_possible_versions(self) -> None:
        self._ui.version.setEditable(False)
        version_in_recipe = self.wizard().recipe_attributes.get("version")
        if version_in_recipe is None:
            # get versions from conandata.yml
            conandata = self.wizard().conandata
            if conandata:
                versions = self._get_versions_from_conandata(conandata)
                if versions:
                    # get the versions from uuids with the same paths
                    for uuid in self.wizard().matching_uuids:
                        with RecipeSettingsReader.from_uuid(uuid) as settings:
                            attributes = settings.attribute_overrides.resolve()
                        if "version" in attributes:
                            self._uuid_versions[attributes["version"]] = uuid

                    with BlockSignals(self._ui.version) as blocked_widget:
                        blocked_widget.clear()
                        model = blocked_widget.model()
                        for i, version in enumerate(versions):
                            if version in self._uuid_versions:
                                blocked_widget.addItem(
                                    QtGui.QIcon(":/cruiz.png"), version
                                )
                                if cruiz.globals.get_main_window().is_recipe_active(
                                    self._uuid_versions[version]
                                ):
                                    item = model.item(i)
                                    item.setFlags(
                                        item.flags() & ~QtGui.Qt.ItemIsEnabled
                                    )
                            else:
                                blocked_widget.addItem(version)
                        blocked_widget.setCurrentIndex(-1)
            else:
                # if the conandata.yml is not available, manually specify a version
                self._ui.version.setEditable(True)
                self._ui.version.lineEdit().setPlaceholderText(
                    "Package version to use, e.g. 1.2.3"
                )
        else:
            with BlockSignals(self._ui.version) as blocked_widget:
                blocked_widget.clear()
                blocked_widget.addItem(version_in_recipe)
            # combobox disabled to ensure it's clear that there's no choice
            self._ui.version.setEnabled(False)

    def _get_versions_from_conandata(
        self, conandata: typing.Dict[str, typing.Dict[str, str]]
    ) -> typing.Optional[typing.List[str]]:
        assert conandata
        with ConanSettingsReader() as settings:
            path_segments = settings.conandata_version_yaml_pathsegment.resolve()
        if not path_segments:
            QtWidgets.QMessageBox.information(
                self,
                "Cannot identify recipe version numbers from conandata.yml file",
                "The conandata.yml beside the recipe cannot be parsed for version "
                "numbers.\n\n"
                "This is because cruiz cannot determine its format without a hint.\n\n"
                "Complete the 'Preferences->Conan->Parsing conandata' setting to "
                "specify how to find the list of version numbers for your recipe.\n\n"
                "For example, if your conandata.yml is formatted as\n\n"
                "\tsources:\n"
                "\t  1.2.3:\n"
                "\t    ...\n"
                "\t  4.5.6:\n"
                "\t    ...\n\n"
                "then specify 'sources' in the preferences.",
            )
            return None
        current_dict = conandata
        for key in path_segments.split("/"):
            if key in current_dict:
                current_dict = conandata[key]  # type: ignore[assignment]
            else:
                QtWidgets.QMessageBox.information(
                    self,
                    "Cannot find YAML path segment in recipe conandata.yml file",
                    f"Unable to locate YAML path segment '{key}' in conandata.yml "
                    f" from preferences expression '{path_segments}'.\n\nThe version "
                    "number can be manually specified, or the preference corrected for "
                    "the YAML layout.",
                )
                return None
        return list(current_dict.keys())
