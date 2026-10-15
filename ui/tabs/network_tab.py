"""Network tab — contact graph, centrality, and mutual contacts.

Dumb tab: receives a pre-built NetworkX graph and DataFrames, renders
them. No analysis happens here.
"""
from __future__ import annotations

import networkx as nx
import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QGroupBox,
    QLabel,
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


class NetworkTab(QWidget):
    """Two-page stack: empty state + graph/table content."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        # Page 0 — Empty
        self.empty = EmptyState(
            icon="🕸️",
            title="No network yet",
            hint="Load a CDR file to see the contact graph.",
        )
        self.stack.addWidget(self.empty)

        # Page 1 — Content
        self.content = self._build_content()
        self.stack.addWidget(self.content)

        self.stack.setCurrentIndex(0)

    # ---------- UI ----------

    def _build_content(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)

        splitter = QSplitter(Qt.Horizontal)

        # Left: graph
        graph_box = QGroupBox("Relationship Network")
        graph_layout = QVBoxLayout(graph_box)
        self.canvas = FigureCanvasQTAgg(Figure(figsize=(6, 5), dpi=90))
        self.ax = self.canvas.figure.add_subplot(111)
        graph_layout.addWidget(self.canvas)
        splitter.addWidget(graph_box)

        # Right: two tables
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        cent_box = QGroupBox("Centrality Ranking (Most Connected)")
        cent_layout = QVBoxLayout(cent_box)
        self.tbl_centrality = DataTable()
        self.model_centrality = PandasModel()
        self.tbl_centrality.setModel(self.model_centrality)
        cent_layout.addWidget(self.tbl_centrality)
        right_layout.addWidget(cent_box, 1)

        mutual_box = QGroupBox("Mutual Contacts (Target A ↔ Target B)")
        mutual_layout = QVBoxLayout(mutual_box)
        self.tbl_mutual = DataTable()
        self.model_mutual = PandasModel()
        self.tbl_mutual.setModel(self.model_mutual)
        mutual_layout.addWidget(self.tbl_mutual)
        right_layout.addWidget(mutual_box, 1)

        splitter.addWidget(right)
        splitter.setSizes([650, 550])

        layout.addWidget(splitter)
        return page

    # ---------- public API ----------

    def update_data(
        self,
        graph: nx.Graph,
        centrality: pd.DataFrame,
        mutual: pd.DataFrame | None = None,
    ) -> None:
        """Refresh the network view.

        Args:
            graph: NetworkX graph from data.analyzer.graph.build_call_graph.
            centrality: DataFrame from data.analyzer.graph.centrality_table.
            mutual: Optional DataFrame from data.analyzer.mutual.mutual_contacts.
        """
        # Update tables
        self.model_centrality.set_dataframe(centrality)

        if mutual is not None and not mutual.empty:
            self.model_mutual.set_dataframe(mutual)
        else:
            self.model_mutual.set_dataframe(
                pd.DataFrame({"Notice": ["Load a Target B CDR to see mutual contacts"]})
            )

        # Draw graph
        self._draw_graph(graph)

        # Flip to content
        self.stack.setCurrentIndex(1)

    def _draw_graph(self, g: nx.Graph) -> None:
        self.ax.clear()

        if g.number_of_nodes() == 0:
            self.ax.text(
                0.5, 0.5, "No connections in dataset",
                ha="center", va="center", fontsize=11, color="#6B7280",
            )
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            self.canvas.figure.tight_layout()
            self.canvas.draw()
            return

        pos = nx.spring_layout(g, k=0.5, seed=42, iterations=50)

        # Compute edge widths relative to max weight
        weights = [g[u][v]["weight"] for u, v in g.edges()]
        max_w = max(weights) if weights else 1
        widths = [0.8 + 3.2 * (w / max_w) for w in weights]

        nx.draw_networkx_nodes(
            g, pos, ax=self.ax,
            node_color="#2563EB",
            node_size=280,
            alpha=0.9,
        )
        nx.draw_networkx_edges(
            g, pos, ax=self.ax,
            width=widths,
            alpha=0.55,
            edge_color="#94A3B8",
        )
        nx.draw_networkx_labels(
            g, pos, ax=self.ax,
            font_size=8,
            font_color="#111827",
        )

        self.ax.set_title(
            f"Network — {g.number_of_nodes()} nodes, {g.number_of_edges()} connections",
            fontsize=10,
            color="#374151",
        )
        self.ax.axis("off")
        self.canvas.figure.tight_layout()
        self.canvas.draw()

    def clear(self) -> None:
        """Return to the empty state."""
        self.stack.setCurrentIndex(0)