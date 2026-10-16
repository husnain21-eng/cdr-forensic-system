"""Network tab — top-connections graph, centrality, and mutual contacts.

Only the top N most-connected nodes are drawn to prevent the "hairball"
effect when a real CDR has hundreds of phone numbers.
"""
from __future__ import annotations

import networkx as nx
import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QGroupBox,
    QLabel,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from ui.components.data_table import DataTable
from ui.components.empty_state import EmptyState
from ui.models.pandas_model import PandasModel


# Show only this many top-connected nodes in the graph.
MAX_GRAPH_NODES = 40

# Label only this many nodes (the top-ranked by degree).
MAX_LABELS = 12


class NetworkTab(QWidget):
    """Two-page stack: empty state + graph/table content."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        self.empty = EmptyState(
            icon="🕸️",
            title="No network yet",
            hint="Load a CDR file to see the contact graph.",
        )
        self.stack.addWidget(self.empty)

        self.content = self._build_content()
        self.stack.addWidget(self.content)

        self.stack.setCurrentIndex(0)

    # ---------- UI ----------

    def _build_content(self) -> QWidget:
        page = QWidget()
        page.setMinimumWidth(900)
        page.setMinimumHeight(560)

        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        # ---- LEFT: graph ----
        graph_box = QGroupBox("Relationship Network")
        graph_layout = QVBoxLayout(graph_box)
        graph_layout.setContentsMargins(8, 8, 8, 8)

        self.canvas = FigureCanvasQTAgg(Figure(figsize=(8, 6), dpi=90))
        self.canvas.setMinimumWidth(460)
        self.canvas.setMinimumHeight(400)
        self.ax = self.canvas.figure.add_subplot(111)
        graph_layout.addWidget(self.canvas)

        # Small explanatory caption
        self.lbl_graph_info = QLabel("")
        self.lbl_graph_info.setStyleSheet(
            "color: #6B7280; font-size: 11px; padding: 2px 4px;"
        )
        self.lbl_graph_info.setWordWrap(True)
        graph_layout.addWidget(self.lbl_graph_info)

        splitter.addWidget(graph_box)

        # ---- RIGHT: two tables, inside a scroll area ----
        right_inner = QWidget()
        right_layout = QVBoxLayout(right_inner)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        cent_box = QGroupBox("Centrality Ranking (Most Connected)")
        cent_layout = QVBoxLayout(cent_box)
        cent_layout.setContentsMargins(8, 8, 8, 8)
        self.tbl_centrality = DataTable()
        self.model_centrality = PandasModel()
        self.tbl_centrality.setModel(self.model_centrality)
        self.tbl_centrality.setMinimumHeight(220)
        cent_layout.addWidget(self.tbl_centrality)
        right_layout.addWidget(cent_box, 1)

        mutual_box = QGroupBox("Mutual Contacts (Target A ↔ Target B)")
        mutual_layout = QVBoxLayout(mutual_box)
        mutual_layout.setContentsMargins(8, 8, 8, 8)
        self.tbl_mutual = DataTable()
        self.model_mutual = PandasModel()
        self.tbl_mutual.setModel(self.model_mutual)
        self.tbl_mutual.setMinimumHeight(180)
        mutual_layout.addWidget(self.tbl_mutual)
        right_layout.addWidget(mutual_box, 1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setMinimumWidth(360)
        scroll.setWidget(right_inner)

        splitter.addWidget(scroll)
        splitter.setSizes([720, 480])

        layout.addWidget(splitter)
        return page

    # ---------- public API ----------

    def update_data(
        self,
        graph: nx.Graph,
        centrality: pd.DataFrame,
        mutual: pd.DataFrame | None = None,
    ) -> None:
        self.model_centrality.set_dataframe(centrality)

        if mutual is not None and not mutual.empty:
            self.model_mutual.set_dataframe(mutual)
        else:
            self.model_mutual.set_dataframe(
                pd.DataFrame(
                    {"Notice": ["Load a Target B CDR to see mutual contacts"]}
                )
            )

        self._draw_graph(graph)
        self.stack.setCurrentIndex(1)

    # ---------- graph rendering ----------

    def _draw_graph(self, g: nx.Graph) -> None:
        self.ax.clear()

        if g.number_of_nodes() == 0:
            self.ax.text(
                0.5, 0.5, "No connections in dataset",
                ha="center", va="center", fontsize=11, color="#6B7280",
            )
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            self.lbl_graph_info.setText("")
            self.canvas.figure.subplots_adjust(
                left=0.02, right=0.98, top=0.96, bottom=0.02
            )
            self.canvas.draw()
            return

        total_nodes = g.number_of_nodes()
        total_edges = g.number_of_edges()

        # --- Keep only the top N nodes by degree ---
        if total_nodes > MAX_GRAPH_NODES:
            degrees = dict(g.degree())
            top_nodes = sorted(
                degrees, key=degrees.get, reverse=True
            )[:MAX_GRAPH_NODES]
            sub = g.subgraph(top_nodes).copy()
            info = (
                f"Showing top {MAX_GRAPH_NODES} most-connected nodes "
                f"(of {total_nodes} total)."
            )
        else:
            sub = g
            info = f"{total_nodes} nodes · {total_edges} connections."

        self.lbl_graph_info.setText(info)

        # --- Layout ---
        # kamada_kawai gives a much cleaner spread than spring_layout
        # for hub-and-spoke networks.
        try:
            pos = nx.kamada_kawai_layout(sub)
        except Exception:
            pos = nx.spring_layout(sub, k=1.5, seed=42, iterations=80)

        # --- Edge weights → widths ---
        weights = [sub[u][v].get("weight", 1) for u, v in sub.edges()]
        max_w = max(weights) if weights else 1
        widths = [0.5 + 2.5 * (w / max_w) for w in weights]

        # --- Draw edges first (behind nodes) ---
        nx.draw_networkx_edges(
            sub, pos, ax=self.ax,
            width=widths,
            alpha=0.35,
            edge_color="#94A3B8",
        )

        # --- Draw nodes ---
        degrees = dict(sub.degree())
        max_deg = max(degrees.values()) if degrees else 1
        # Size: hub nodes bigger, small nodes smaller
        node_sizes = [
            80 + 500 * (degrees[n] / max_deg) for n in sub.nodes()
        ]
        nx.draw_networkx_nodes(
            sub, pos, ax=self.ax,
            node_color="#2563EB",
            node_size=node_sizes,
            alpha=0.92,
        )

        # --- Label only the top-N nodes ---
        top_by_degree = sorted(
            sub.nodes(), key=lambda n: degrees[n], reverse=True
        )[:MAX_LABELS]
        labels = {n: self._short(n) for n in top_by_degree}
        nx.draw_networkx_labels(
            sub, pos, labels=labels, ax=self.ax,
            font_size=8, font_color="#111827",
        )

        self.ax.set_title(
            f"Top-{min(MAX_GRAPH_NODES, total_nodes)} Nodes Network",
            fontsize=11,
            color="#374151",
        )
        self.ax.axis("off")
        self.canvas.figure.subplots_adjust(
            left=0.02, right=0.98, top=0.94, bottom=0.02
        )
        self.canvas.draw()

    @staticmethod
    def _short(label: str, max_len: int = 14) -> str:
        s = str(label)
        return s if len(s) <= max_len else s[:max_len - 1] + "…"

    def clear(self) -> None:
        self.stack.setCurrentIndex(0)