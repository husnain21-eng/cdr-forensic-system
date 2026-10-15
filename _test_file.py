"""Temporary test for DashboardTab. Delete after verifying."""
import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget

from data.analyzer.anomalies import summary
from data.analyzer.risk import compute_risk
from data.loader import load_single_file
from ui.tabs.dashboard_tab import DashboardTab
from ui.theme.palette import LIGHT
from ui.theme.stylesheet import stylesheet


class Demo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dashboard tab test")
        self.resize(1100, 600)
        self.setStyleSheet(stylesheet(LIGHT))

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        self.dashboard = DashboardTab()
        layout.addWidget(self.dashboard, 1)

        btn = QPushButton("Load sample_cdr.csv → update dashboard")
        btn.clicked.connect(self._load)
        layout.addWidget(btn)

        btn_clear = QPushButton("Clear → show empty state")
        btn_clear.clicked.connect(self.dashboard.clear)
        layout.addWidget(btn_clear)

    def _load(self):
        df = load_single_file("sample_cdr.csv")
        risk = compute_risk(df)
        anoms = summary(df)
        self.dashboard.update_data(df, risk, anoms)


app = QApplication(sys.argv)
w = Demo()
w.show()
sys.exit(app.exec_())