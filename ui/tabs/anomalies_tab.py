"""Anomalies tab — forensic red flags.

Shows short calls, night calls, and a summary count. Dumb tab — the
main window passes in pre-filtered DataFrames.
"""
from __future__ import annotations

import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ui.components.data_table import DataTable
from ui.components.empty_state import EmptyState
from ui.models.pandas_model import PandasModel


class AnomaliesTab(QWidget):
    """Two-page stack: empty state + anomaly tables."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        # Page 0 — Empty
        self.empty = EmptyState(
            icon="🚨",
            title="No anomalies to show",
            hint="Load a CDR file to detect short calls and night activity.",
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

        # Summary row
        summary_box = QGroupBox("Summary")
        summary_layout = QHBoxLayout(summary_box)

        self.lbl_total = self._make_stat_label("0", "Total records")
        self.lbl_short = self._make_stat_label("0", "Short calls (≤5s)")
        self.lbl_night = self._make_stat_label("0", "Night calls (23:00–05:00)")

        summary_layout.addWidget(self.lbl_total)
        summary_layout.addWidget(self.lbl_short)
        summary_layout.addWidget(self.lbl_night)
        summary_layout.addStretch()

        layout.addWidget(summary_box)

        # Two tables in a splitter
        splitter = QSplitter(Qt.Vertical)

        short_box = QGroupBox("Short Calls — Possible Missed-Ping Pattern")
        short_layout = QVBoxLayout(short_box)
        self.tbl_short = DataTable()
        self.model_short = PandasModel()
        self.tbl_short.setModel(self.model_short)
        short_layout.addWidget(self.tbl_short)
        splitter.addWidget(short_box)

        night_box = QGroupBox("Night Activity — Unusual Hours (23:00–05:00)")
        night_layout = QVBoxLayout(night_box)
        self.tbl_night = DataTable()
        self.model_night = PandasModel()
        self.tbl_night.setModel(self.model_night)
        night_layout.addWidget(self.tbl_night)
        splitter.addWidget(night_box)

        splitter.setSizes([350, 350])
        layout.addWidget(splitter, 1)

        return page

    def _make_stat_label(self, value: str, caption: str) -> QWidget:
        """Create a large-number + small-caption stat block."""
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 4, 24, 4)
        layout.setSpacing(0)

        value_label = QLabel(value)
        value_label.setStyleSheet(
            "font-size: 24px; font-weight: 700; color: #111827;"
        )
        value_label.setObjectName("value")

        caption_label = QLabel(caption)
        caption_label.setStyleSheet(
            "font-size: 11px; color: #6B7280;"
        )

        layout.addWidget(value_label)
        layout.addWidget(caption_label)

        # Store value label on the parent for later updates
        w._value_label = value_label  # type: ignore[attr-defined]
        return w

    # ---------- public API ----------

    def update_data(
        self,
        short_df: pd.DataFrame,
        night_df: pd.DataFrame,
        summary: dict,
    ) -> None:
        """Refresh the tab.

        Args:
            short_df: Rows from data.analyzer.anomalies.short_calls.
            night_df: Rows from data.analyzer.anomalies.night_calls.
            summary: Dict from data.analyzer.anomalies.summary.
        """
        # Summary counts
        self.lbl_total._value_label.setText(f"{summary.get('total', 0):,}")  # type: ignore[attr-defined]
        self.lbl_short._value_label.setText(f"{summary.get('short_calls', 0):,}")  # type: ignore[attr-defined]
        self.lbl_night._value_label.setText(f"{summary.get('night_calls', 0):,}")  # type: ignore[attr-defined]

        # Tables
        self.model_short.set_dataframe(
            self._filter_columns(short_df)
        )
        self.model_night.set_dataframe(
            self._filter_columns(night_df)
        )

        self.stack.setCurrentIndex(1)

    def _filter_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return a slimmed-down DataFrame with only the useful columns."""
        if df.empty:
            return df

        wanted = [
            c for c in [
                "party_a", "party_b", "timestamp",
                "duration_sec", "hour", "cell_id",
            ]
            if c in df.columns
        ]
        return df[wanted].reset_index(drop=True)

    def clear(self) -> None:
        """Return to the empty state."""
        self.stack.setCurrentIndex(0)