#!/usr/bin/env python3

"""
Conan dependency view
"""

import typing

# TODO: note, change, as QtSvgWidgets wasn't available here previously
from qtpy import QtWidgets, QtSvg, QtSvgWidgets

from cruiz.interop.dependencygraph import DependencyGraph
from cruiz.svggraph import DependenciesToDigraph, DigraphToSVG, SVGScene


class DependencyView(QtWidgets.QGraphicsView):
    def clear(self) -> None:
        self.setScene(None)

    def visualise(self, depgraph: DependencyGraph, rankdir: int) -> None:
        if rankdir == 0:
            rank_dir = "LR"
        elif rankdir == 1:
            rank_dir = "TB"
        digraph = DependenciesToDigraph(depgraph, rank_dir)
        svg = DigraphToSVG(digraph)
        self._scene = SVGScene(QtSvg.QSvgRenderer(svg.svg))
        self.setScene(self._scene)


class InverseDependencyViewDialog(QtWidgets.QDialog):
    def __init__(
        self,
        depgraph: DependencyGraph,
        parent: typing.Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"What uses {depgraph.root.name}")

        # TODO: should this be in cruiz.svggraph to isolate the SVG code?
        digraph = DependenciesToDigraph(depgraph, "LR", flipped_edges=True)
        svg = DigraphToSVG(digraph)
        self._renderer = QtSvg.QSvgRenderer(svg.svg)
        item = QtSvgWidgets.QGraphicsSvgItem()
        item.setSharedRenderer(self._renderer)
        self._scene = QtWidgets.QGraphicsScene()
        self._scene.addItem(item)
        view = QtWidgets.QGraphicsView(self._scene)

        QtWidgets.QVBoxLayout(self).addWidget(view)
