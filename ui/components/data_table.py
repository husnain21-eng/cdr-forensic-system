"""Enhanced QTableView with sorting, copy, and CSV export.

Features enabled by default:
  - Zebra striping
  - Full-row selection
  - Click-to-sort columns
  - Ctrl+C copies selected rows (tab-separated)
  - Ctrl+S exports the entire table as CSV
"""
from __future__ import annotations

import csv

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QTableView,
    QShortcut,
)


class DataTable(QTableView):
    """A pre-configured table view for pandas-backed data."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.ExtendedSelection)
        self.setSortingEnabled(True)
        self.setShowGrid(False)
        self.verticalHeader().setDefaultSectionSize(32)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)

        # Keyboard shortcuts
        QShortcut(QKeySequence.Copy, self, activated=self._copy_selection)
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self._export_csv)

    # ---------- actions ----------

    def _copy_selection(self) -> None:
        """Copy selected rows to clipboard as tab-separated text."""
        indexes = self.selectionModel()
        if indexes is None:
            return

        rows = sorted({i.row() for i in indexes.selectedRows()})
        if not rows:
            return

        model = self.model()
        if model is None:
            return

        lines = []
        for r in rows:
            cells = [
                model.data(model.index(r, c)) or ""
                for c in range(model.columnCount())
            ]
            lines.append("\t".join(cells))

        QApplication.clipboard().setText("\n".join(lines))

    def _export_csv(self) -> None:
        """Export the full table to a user-selected CSV file."""
        model = self.model()
        if model is None:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export table as CSV",
            "table.csv",
            "CSV Files (*.csv)",
        )
        if not path:
            return

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            header = [
                model.headerData(c, Qt.Horizontal)
                for c in range(model.columnCount())
            ]
            writer.writerow(header)
            for r in range(model.rowCount()):
                writer.writerow([
                    model.data(model.index(r, c)) or ""
                    for c in range(model.columnCount())
                ])