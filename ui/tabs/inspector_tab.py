"""Inspector tab — raw CDR data browser with live search.

Full row-level view of the loaded dataset with a filter box that
matches across every column.
"""
from __future__ import annotations

import pandas as pd
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ui.components.data_table import DataTable
from ui.components.empty_state import EmptyState
from ui.models.pandas_model import PandasModel


class InspectorTab(QWidget):
    """Two-page stack: empty state + searchable raw data table."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self._df: pd.DataFrame = pd.DataFrame()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        # Page 0 — Empty
        self.empty = EmptyState(
            icon="🔍",
            title="No raw data yet",
            hint="Load a CDR file to browse the raw records.",
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
        layout.setSpacing(10)

        # Search row
        search_row = QHBoxLayout()

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText(
            "Filter across all columns… (case-insensitive)"
        )
        self.txt_search.setClearButtonEnabled(True)
        self.txt_search.textChanged.connect(self._apply_filter)

        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet("color: #6B7280; font-size: 14px;")

        search_row.addWidget(self.txt_search, 1)
        search_row.addWidget(self.lbl_count)

        layout.addLayout(search_row)

        # Data table
        self.table = DataTable()
        self.model = PandasModel()
        self.table.setModel(self.model)
        layout.addWidget(self.table, 1)

        return page

    # ---------- public API ----------

    def update_data(self, df: pd.DataFrame) -> None:
        """Replace the underlying dataset and refresh the view."""
        self._df = df.copy() if not df.empty else pd.DataFrame()

        if self._df.empty:
            self.stack.setCurrentIndex(0)
            return

        self._apply_filter(self.txt_search.text())
        self.stack.setCurrentIndex(1)

    def clear(self) -> None:
        """Return to the empty state."""
        self._df = pd.DataFrame()
        self.txt_search.clear()
        self.model.set_dataframe(pd.DataFrame())
        self.stack.setCurrentIndex(0)

    # ---------- filtering ----------

    def _apply_filter(self, query: str) -> None:
        if self._df.empty:
            return

        query = query.strip().lower()

        if not query:
            filtered = self._df
        else:
            # Match any cell containing the query (all columns, all rows)
            mask = self._df.astype(str).apply(
                lambda col: col.str.lower().str.contains(
                    query, na=False, regex=False
                )
            ).any(axis=1)
            filtered = self._df[mask]

        # Reset index so the table shows clean row numbers
        filtered = filtered.reset_index(drop=True)

        self.model.set_dataframe(filtered)

        total = len(self._df)
        shown = len(filtered)
        if shown == total:
            self.lbl_count.setText(f"{total:,} rows")
        else:
            self.lbl_count.setText(f"{shown:,} of {total:,} rows")