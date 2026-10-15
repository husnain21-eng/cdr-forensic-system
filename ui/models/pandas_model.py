"""QAbstractTableModel adapter for pandas DataFrames.

Lets any QTableView display a DataFrame with a single method call:
    model.set_dataframe(df)
"""
from __future__ import annotations

import pandas as pd
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt


class PandasModel(QAbstractTableModel):
    """Read-only DataFrame → Qt table model."""

    def __init__(self, df: pd.DataFrame | None = None, parent=None):
        super().__init__(parent)
        self._df = df if df is not None else pd.DataFrame()

    def set_dataframe(self, df: pd.DataFrame) -> None:
        """Replace the underlying DataFrame and refresh the view."""
        self.beginResetModel()
        self._df = df if df is not None else pd.DataFrame()
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return self._df.shape[0]

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return self._df.shape[1]

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        try:
            value = self._df.iat[index.row(), index.column()]
        except IndexError:
            return None
        return "" if pd.isna(value) else str(value)

    def headerData(
        self,
        section: int,
        orientation: int,
        role: int = Qt.DisplayRole,
    ):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            if section < len(self._df.columns):
                return str(self._df.columns[section])
            return None
        return str(section + 1)