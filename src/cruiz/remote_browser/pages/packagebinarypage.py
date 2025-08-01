#!/usr/bin/env python3

"""Remote browser page."""

from __future__ import annotations

import html
import pathlib
import shutil
import tarfile
import tempfile
import typing

from PySide6 import QtCore, QtGui, QtWebEngineCore, QtWidgets

import cruiz.globals
from cruiz.interop.packagebinaryparameters import PackageBinaryParameters
from cruiz.pyside6.remote_browser_fileview import Ui_remote_browser_fileview

from .page import Page

if typing.TYPE_CHECKING:
    from cruiz.pyside6.remote_browser import Ui_remotebrowser


class _FileNode:
    def __init__(self, path: str, parent: typing.Optional[_FileNode]):
        self.path = path
        self.parent = parent
        self.children: typing.List[_FileNode] = []
        self.is_file = True
        self.link_target: typing.Optional[str] = None
        self.container: typing.Optional[str] = None
        self.is_container = False
        # am hoping this is reusable on the same tarball but outside the context manager
        self.tar_info: typing.Optional[tarfile.TarInfo] = None

    def add_child(self, path: str) -> _FileNode:
        """Add a child path."""
        find = [x for x in self.children if x.path == path]
        if find:
            assert len(find) == 1
            return find[0]
        node = _FileNode(path, self)
        self.children.append(node)
        return node

    def add_tarball(
        self, directory: pathlib.Path, tarball_basename: str, parent: _FileNode
    ) -> None:
        """Add a tarball containing many children."""
        tar_node = parent.add_child(tarball_basename)
        tar_node.is_container = True
        tarball_path = directory / tarball_basename
        with tarfile.open(tarball_path, "r") as tar:
            for tarinfo in tar:
                path = pathlib.PurePosixPath(tarinfo.name)
                parent = tar_node
                combined_path = pathlib.PurePosixPath()
                for part in path.parts:
                    combined_path /= part
                    parent = parent.add_child(str(combined_path))
                    parent.is_file = False
                    parent.container = tarball_basename
                if tarinfo.isfile():
                    parent.is_file = True  # the leaf is a file
                    parent.tar_info = tarinfo
                else:
                    if tarinfo.issym():
                        parent.is_file = True  # the leaf is a file
                        parent.link_target = tarinfo.linkname  # and also a symlink
                    else:
                        raise AssertionError(
                            f"Unknown entity type for '{tarinfo.name}'"
                        )

    @property
    def child_index(self) -> int:
        """Get the child index of this node in relation to its parent."""
        if self.parent:
            return self.parent.children.index(self)
        return 0


class _PackageBinaryModel(QtCore.QAbstractItemModel):
    def __init__(self, parent: QtCore.QObject) -> None:
        super().__init__(parent)
        self._root: typing.Optional[_FileNode] = None
        self._parent_object = parent

    def set(
        self,
        results: typing.Optional[typing.List[str]],
        folder: typing.Optional[pathlib.Path],
    ) -> None:
        """Set the results against the model."""
        self.beginResetModel()
        if results:
            assert folder
            self._root = _FileNode("/", None)
            self._root.is_file = False
            for file in results:
                if file.endswith(".tgz"):
                    self._root.add_tarball(folder, file, self._root)
                else:
                    self._root.add_child(file)
        else:
            self._root = None
        self.endResetModel()

    def rowCount(self, parent) -> int:  # type: ignore
        """Get the number of rows in the model."""
        if self._root is None:
            return 0
        if parent.isValid():
            node = parent.internalPointer()
            return len(node.children)
        return 1

    def columnCount(self, parent) -> int:  # type: ignore
        """Get the number of columns in the model."""
        # pylint: disable=unused-argument
        if self._root is None:
            return 0
        return 1

    def parent(self, index) -> QtCore.QModelIndex:  # type: ignore
        """Get the index's parent."""
        if not index.isValid():
            return QtCore.QModelIndex()
        node = index.internalPointer()
        if node.parent is None:
            return QtCore.QModelIndex()
        return super().createIndex(node.parent.child_index, 0, node.parent)

    def index(self, row, column, parent):  # type: ignore
        """Get the model index given the coordinates."""
        if not parent.isValid():
            return super().createIndex(row, column, self._root)
        parent_node = parent.internalPointer()
        node = parent_node.children[row]
        return super().createIndex(row, column, node)

    def headerData(self, section, orientation, role):  # type: ignore
        """Get the header data from the model."""
        if (
            role == QtCore.Qt.ItemDataRole.DisplayRole
            and orientation == QtCore.Qt.Orientation.Horizontal
            and not section
        ):
            return "Path"
        return None

    def data(self, index, role):  # type: ignore
        """Get data from the model."""
        node = index.internalPointer()
        if role == QtCore.Qt.ItemDataRole.DisplayRole and not index.column():
            return pathlib.Path(node.path).name
        if (
            role == QtCore.Qt.ItemDataRole.ToolTipRole
            and not index.column()
            and node.is_file
            and node.link_target
        ):
            return f"Symbolic link to {node.link_target}"
        if role == QtCore.Qt.ItemDataRole.DecorationRole and not index.column():
            if node.is_file:
                if node.link_target:
                    assert isinstance(self._parent_object, PackageBinaryPage)
                    return self._parent_object.style().standardIcon(
                        QtWidgets.QStyle.StandardPixmap.SP_FileLinkIcon
                    )
            else:
                return QtWidgets.QFileIconProvider().icon(
                    QtGui.QAbstractFileIconProvider.IconType.Folder
                )
        return None

    def flags(self, index):  # type: ignore
        """Get the flags from a model index."""
        default_flags = super().flags(index)
        node = index.internalPointer()
        if node.link_target:
            return default_flags & ~QtCore.Qt.ItemFlag.ItemIsEnabled
        return default_flags


class _FileViewer(QtWidgets.QDialog):
    def __init__(
        self,
        root: pathlib.Path,
        path: pathlib.Path,
        container: pathlib.Path,
        parent: typing.Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._ui = Ui_remote_browser_fileview()
        self._ui.setupUi(self)  # type: ignore[no-untyped-call]
        self._ui.fileview.page().settings().setAttribute(
            QtWebEngineCore.QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls,  # noqa: E501
            True,
        )
        if container:
            html_path = _FileViewer._write_html(path, root / container)
            self.setWindowTitle(f"{path} in {container}")
        else:
            html_path = _FileViewer._write_html(root / path, None)
            self.setWindowTitle(str(path))
        self._ui.fileview.load(QtCore.QUrl.fromLocalFile(str(html_path)))

    @staticmethod
    def _write_html(
        path: pathlib.Path, archive: typing.Optional[pathlib.Path]
    ) -> pathlib.Path:
        if archive:
            with tarfile.open(archive, "r") as tar:
                tar.extract(str(path), path=archive.parent)
            with (archive.parent / path).open("rt", encoding="utf-8") as data_file:
                contents = data_file.readlines()
            html_path = archive.parent / path
            html_path = html_path.with_suffix(".html")
        else:
            with path.open("rt", encoding="utf-8") as data_file:
                contents = data_file.readlines()
            html_path = pathlib.Path(path.with_suffix(".html"))
        html_path.parent.mkdir(parents=True, exist_ok=True)
        with html_path.open("wt", encoding="utf-8") as html_file:
            url_start = "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0"
            html_file.write("<html>")
            html_file.write("<head>")
            if cruiz.globals.is_dark_theme():
                html_file.write(
                    f'<link rel="stylesheet" href="{url_start}/styles/dark.min.css">'
                )
            else:
                html_file.write(
                    f'<link rel="stylesheet" href="{url_start}/styles/default.min.css">'
                )
            html_file.write(f'<script src="{url_start}/highlight.min.js"></script>')
            html_file.write(
                '<script src="https://cdnjs.cloudflare.com/ajax/libs/highlightjs-line-numbers.js/2.8.0/highlightjs-line-numbers.min.js"></script>'  # noqa: E501
            )
            html_file.write("<script>hljs.highlightAll();</script>")
            html_file.write("<script>hljs.initLineNumbersOnLoad();</script>")
            html_file.write("</head>")
            html_file.write('<body style="margin: 0; padding: 0">')
            html_file.write("<pre><code>")
            # with line numbers enabled, we lose leading spaces with html.escape,
            # so put them back manually per line
            for line in contents:
                trimmed = line.lstrip()
                if not trimmed:
                    html_file.write(line)  # honour empty lines
                    continue
                escaped = html.escape(trimmed)
                if len(trimmed) == len(line):
                    html_file.write(escaped)
                    continue
                nbsp_prefix = "&nbsp;" * (len(line) - len(trimmed))
                html_file.write(nbsp_prefix + escaped)
            html_file.write("</code></pre>")
            html_file.write("</body>")
            html_file.write("</html>")
        return html_path


class PackageBinaryPage(Page):
    """Remote browser page for displaying package binaries."""

    def setup(self, self_ui: Ui_remotebrowser) -> None:
        """Set up the UI for the page."""
        self._base_setup(self_ui, 4)
        self._current_pkgref: typing.Optional[str] = None
        self._artifact_folder: typing.Optional[pathlib.Path] = None
        self._model = _PackageBinaryModel(self)
        self._ui.package_binary.setModel(self._model)
        self._ui.package_binary.customContextMenuRequested.connect(self._on_file_menu)

        self._ui.package_binary.doubleClicked.connect(self._on_prev_dclicked)
        self._ui.pbinary_back.clicked.connect(self._on_back)
        self._ui.pbinary_cancel.clicked.connect(self.on_cancel)
        self._ui.pbinary_restart.clicked.connect(self._on_restart)
        self._ui.pbinary_pkgref.customContextMenuRequested.connect(self._on_pkgref_menu)

    def _enable_progress(self, enable: bool) -> None:
        self._ui.pbinary_progress.setMaximum(0 if enable else 1)
        self._ui.pbinary_buttons.setEnabled(not enable)
        self._ui.pbinary_cancel.setEnabled(enable)

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        """Override the widget's showEvent method."""
        # pylint: disable=unused-argument
        pkgref = self._previous_pkgref
        self._ui.pbinary_pkgref.setText(pkgref)

        if self._current_pkgref != pkgref:
            self._artifact_folder = pathlib.Path(tempfile.mkdtemp(suffix="cruiz"))
            self._model.set(None, None)
            self._enable_progress(True)
            self._ui.pbinary_groupbox.setEnabled(False)
            params = PackageBinaryParameters(
                reference=pkgref,
                remote_name=self._ui.remote.currentText(),
                where=self._artifact_folder,
            )
            self._context.get_package_details(params, self._complete)

    def _complete(self, results: typing.Any, exception: typing.Any) -> None:
        self._enable_progress(False)
        if exception:
            self._log_details.stderr(str(exception))
            return
        if results is not None:
            self._model.set(results, self._artifact_folder)
            self._ui.package_binary.expandAll()
            self._ui.pbinary_groupbox.setEnabled(True)
            self._current_pkgref = self._previous_pkgref

    def _on_back(self) -> None:
        if self._revisions_enabled:
            self._ui.stackedWidget.setCurrentWidget(self._ui.prev)
        else:
            self._ui.stackedWidget.setCurrentWidget(self._ui.package_id)

    def _on_prev_dclicked(self, index: QtCore.QModelIndex) -> None:
        node = index.internalPointer()
        if not node.is_file:
            return
        path = node.path
        container = node.container
        try:
            assert self._artifact_folder
            _FileViewer(self._artifact_folder, path, container, self).exec_()
        except UnicodeDecodeError:
            QtWidgets.QMessageBox.critical(
                self,
                "Cannot view file contents",
                f"Unable to interpret file {path} in archive {container} " "as text",
                QtWidgets.QMessageBox.StandardButton.Ok,
                QtWidgets.QMessageBox.StandardButton.NoButton,
            )

    def on_cancel(self) -> None:
        """Call when the user cancels the operation."""
        self._context.cancel()
        self._enable_progress(False)

    def _on_restart(self) -> None:
        self._open_start()

    def _on_copy_pkgref_to_clip(self) -> None:
        QtWidgets.QApplication.clipboard().setText(self._ui.pbinary_pkgref.text())

    def _on_file_menu(self, position: QtCore.QPoint) -> None:
        selection = self._ui.package_binary.selectedIndexes()
        assert len(selection) == 1
        node = selection[0].internalPointer()
        if not node.is_file:
            return
        if node.link_target:
            return
        menu = QtWidgets.QMenu(self)
        save_action = QtGui.QAction("Save ...", self)
        save_action.triggered.connect(self._on_file_save)
        menu.addAction(save_action)
        sender_treeview = self.sender()
        assert isinstance(sender_treeview, QtWidgets.QTreeView)
        menu.exec_(sender_treeview.mapToGlobal(position))

    def _on_file_save(self) -> None:
        selection = self._ui.package_binary.selectedIndexes()
        assert len(selection) == 1
        node = selection[0].internalPointer()
        new_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, f"Save {node.path} from package", "", ""
        )
        if not new_path:
            return
        if node.container:
            with tarfile.open(self._artifact_folder / node.container, "r") as tar:
                contents_object = tar.extractfile(node.tar_info)
                assert contents_object
                new_path_path = pathlib.Path(new_path)
                with new_path_path.open("wb") as writer:
                    writer.write(contents_object.read())
        else:
            shutil.copyfile(self._artifact_folder / node.path, new_path)
