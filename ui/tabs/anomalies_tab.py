"""Anomalies tab — forensic red flags including statistical Z-scores."""
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

        self.empty = EmptyState(
            icon="🚨",
            title="No anomalies to show",
            hint="Load a CDR file to detect short calls, night activity, and statistical outliers.",
        )
        self.stack.addWidget(self.empty)

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
        self.lbl_stat = self._make_stat_label("0", "Statistical Anomalies (Z>2.5)")

        summary_layout.addWidget(self.lbl_total)
        summary_layout.addWidget(self.lbl_short)
        summary_layout.addWidget(self.lbl_night)
        summary_layout.addWidget(self.lbl_stat)
        summary_layout.addStretch()

        layout.addWidget(summary_box)

        # Three tables in a splitter
        splitter = QSplitter(Qt.Vertical)
        splitter.setChildrenCollapsible(False)

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

        stat_box = QGroupBox("Statistical Anomalies — Abnormal Call Volume (Z-Score > 2.5)")
        stat_layout = QVBoxLayout(stat_box)
        self.tbl_stat = DataTable()
        self.model_stat = PandasModel()
        self.tbl_stat.setModel(self.model_stat)
        stat_layout.addWidget(self.tbl_stat)
        splitter.addWidget(stat_box)

        # Give them equal height
        splitter.setSizes([250, 250, 250])
        layout.addWidget(splitter, 1)

        return page

    def _make_stat_label(self, value: str, caption: str) -> QWidget:
        """Create a large-number + small-caption stat block."""
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 4, 16, 4)
        layout.setSpacing(0)

        value_label = QLabel(value)
        value_label.setStyleSheet(
            "font-size: 20px; font-weight: 700; color: #111827;"
        )
        value_label.setObjectName("value")

        caption_label = QLabel(caption)
        caption_label.setStyleSheet(
            "font-size: 11px; color: #6B7280;"
        )

        layout.addWidget(value_label)
        layout.addWidget(caption_label)

        w._value_label = value_label  # type: ignore[attr-defined]
        return w

    # ---------- public API ----------

    def update_data(
            self,
            short_df: pd.DataFrame,
            night_df: pd.DataFrame,
            summary: dict,
            stat_df: pd.DataFrame | None = None,
    ) -> None:
        """Refresh the tab with new data."""

        # Update summary counts
        self.lbl_total._value_label.setText(f"{summary.get('total', 0):,}")  # type: ignore[attr-defined]
        self.lbl_short._value_label.setText(f"{summary.get('short_calls', 0):,}")  # type: ignore[attr-defined]
        self.lbl_night._value_label.setText(f"{summary.get('night_calls', 0):,}")  # type: ignore[attr-defined]

        if stat_df is not None:
            self.lbl_stat._value_label.setText(f"{len(stat_df):,}")  # type: ignore[attr-defined]
        else:
            self.lbl_stat._value_label.setText("0")  # type: ignore[attr-defined]

        # Update tables
        self.model_short.set_dataframe(self._filter_columns(short_df))
        self.model_night.set_dataframe(self._filter_columns(night_df))

        if stat_df is not None and not stat_df.empty:
            self.model_stat.set_dataframe(stat_df)
        else:
            self.model_stat.set_dataframe(
                pd.DataFrame(columns=["party_a", "date", "call_count", "mean", "std", "z_score"])
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