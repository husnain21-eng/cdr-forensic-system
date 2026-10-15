"""Temporary test for the DataTable component. Delete after verifying."""
import sys

import pandas as pd
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

from ui.components.data_table import DataTable
from ui.models.pandas_model import PandasModel
from ui.theme.palette import LIGHT
from ui.theme.stylesheet import stylesheet


class Demo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DataTable test — try Ctrl+C and Ctrl+S")
        self.resize(900, 500)
        self.setStyleSheet(stylesheet(LIGHT))

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Sample data
        df = pd.DataFrame({
            "Party A": ["111-222-3333", "444-555-6666", "777-888-9999", "111-222-3333"],
            "Party B": ["444-555-6666", "111-222-3333", "111-222-3333", "999-888-7777"],
            "Duration": [45, 3, 120, 8],
            "Hour": [10, 23, 2, 14],
            "Tower": ["TWR-01", "TWR-02", "TWR-01", "TWR-03"],
        })

        self.table = DataTable()
        self.table.setModel(PandasModel(df))
        layout.addWidget(self.table)


app = QApplication(sys.argv)
w = Demo()
w.show()
sys.exit(app.exec_())