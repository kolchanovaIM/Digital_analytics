import os
import shutil

from graphviz import Digraph
from PyQt6.QtWidgets import QFileDialog


class GraphvizGenerator:
    def __init__(self, parent=None):
        self.parent = parent
        self.dot_path = self.find_graphviz()

    def find_graphviz(self):

        dot = shutil.which("dot")

        if dot:
            return dot

        common_paths = [
            r"C:\Program Files\Graphviz\bin\dot.exe",
            r"C:\Program Files (x86)\Graphviz\bin\dot.exe",
            "/usr/bin/dot",
            "/opt/homebrew/bin/dot"
        ]

        for path in common_paths:
            if os.path.exists(path):
                return path

        path, _ = QFileDialog.getOpenFileName(
            self.parent,
            "Укажите путь к dot.exe",
            "",
            "Executable (*.exe)"
        )

        return path

    def build_graph(self, nodes, edges):

        graph = Digraph("Flowchart")

        graph.attr(rankdir="TB")
        graph.attr(splines="ortho")
        graph.attr(nodesep="0.7")
        graph.attr(ranksep="0.8")

        graph.attr(
            "node",
            fontname="Arial",
            fontsize="12",
            style="rounded,filled",
            fillcolor="white"
        )

        graph.attr(
            "edge",
            fontname="Arial",
            fontsize="10",
            arrowsize="0.8"
        )

        # =========================================
        # УЗЛЫ
        # =========================================

        for node in nodes:

            if node.shape == "merge":

                graph.node(
                    node.node_id,
                    "",
                    shape="point",
                    width="0.01"
                )

                continue

            shape = "box"

            if node.shape == "oval":
                shape = "ellipse"

            elif node.shape == "diamond":
                shape = "diamond"

            elif node.shape == "parallelogram":
                shape = "parallelogram"

            graph.node(
                node.node_id,
                node.text,
                shape=shape
            )

        # =========================================
        # РЁБРА
        # =========================================

        for edge in edges:

            attrs = {}

            if edge.label:
                attrs["label"] = edge.label

            if edge.is_back_edge:
                attrs["constraint"] = "false"
                attrs["headport"] = "n"

            graph.edge(
                edge.source,
                edge.target,
                **attrs
            )

        return graph