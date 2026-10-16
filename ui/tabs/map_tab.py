"""Map tab — Folium map controls and tower frequency table.

Emits `launch_map_requested` when the user clicks "Launch Map". The
main window handles the actual map generation.
"""
from __future__ import annotations

import pandas as pd
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ui.components.data_table import DataTable
from ui.components.empty_state import EmptyState
from ui.models.pandas_model import PandasModel


class MapTab(QWidget):
    """Two-page stack: empty state + map controls."""

    launch_map_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        # Page 0 — Empty
        self.empty = EmptyState(
            icon="🗺️",
            title="No map data yet",
            hint="Load a CDR file with lat/lon values to enable the map.",
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
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Layer controls
        controls_box = QGroupBox("Map Layers")
        controls_layout = QHBoxLayout(controls_box)

        self.chk_heatmap = QCheckBox("🔥 Density heatmap")
        self.chk_triangulation = QCheckBox("📡 Triangulation radii")
        self.chk_triangulation.setChecked(True)
        self.chk_colocation = QCheckBox("⭐ Co-location events")
        self.chk_colocation.setChecked(True)

        controls_layout.addWidget(self.chk_heatmap)
        controls_layout.addWidget(self.chk_triangulation)
        controls_layout.addWidget(self.chk_colocation)
        controls_layout.addStretch()

        layout.addWidget(controls_box)

        # Action row
        action_row = QHBoxLayout()

        self.lbl_hint = QLabel(
            "Click <b>Launch Intelligence Map</b> to open an interactive map "
            "in your browser."
        )
        self.lbl_hint.setStyleSheet("color: #6B7280; font-size: 14px;")

        self.btn_launch = QPushButton("🗺️  Launch Intelligence Map")
        self.btn_launch.setProperty("role", "primary")
        self.btn_launch.setMinimumHeight(40)
        self.btn_launch.clicked.connect(self.launch_map_requested.emit)

        action_row.addWidget(self.lbl_hint, 1)
        action_row.addWidget(self.btn_launch)

        layout.addLayout(action_row)

        # Tower frequency table
        tower_box = QGroupBox("Cell Towers / Sites Frequency")
        tower_layout = QVBoxLayout(tower_box)

        self.tbl_towers = DataTable()
        self.model_towers = PandasModel()
        self.tbl_towers.setModel(self.model_towers)
        tower_layout.addWidget(self.tbl_towers)

        layout.addWidget(tower_box, 1)

        return page

    # ---------- public API ----------

    def update_data(self, df: pd.DataFrame) -> None:
        """Refresh the tab with new data.

        Args:
            df: Normalized CDR DataFrame (must have 'cell_id' if available).
        """
        if df.empty:
            self.stack.setCurrentIndex(0)
            return

        # Tower table
        if "cell_id" in df.columns and df["cell_id"].notna().any():
            counts = (
                df["cell_id"]
                .dropna()
                .astype(str)
                .value_counts()
                .reset_index()
            )
            counts.columns = ["Tower / Site ID", "Records"]
            self.model_towers.set_dataframe(counts)
        else:
            self.model_towers.set_dataframe(
                pd.DataFrame({"Notice": ["No cell_id column in dataset"]})
            )

        self.stack.setCurrentIndex(1)

    # ---------- state ----------

    def heatmap_enabled(self) -> bool:
        return self.chk_heatmap.isChecked()

    def triangulation_enabled(self) -> bool:
        return self.chk_triangulation.isChecked()

    def colocation_enabled(self) -> bool:
        return self.chk_colocation.isChecked()

    def clear(self) -> None:
        """Return to the empty state."""
        self.stack.setCurrentIndex(0)