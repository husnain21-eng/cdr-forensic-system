"""Temporary test for NetworkTab. Delete after verifying."""
import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget

from data.analyzer.graph import build_call_graph, centrality_table
from data.analyzer.mutual import mutual_contacts
from data.loader import load_single_file
from ui.tabs.network_tab import NetworkTab
from ui.theme.palette import LIGHT
from ui.theme.stylesheet import stylesheet


class Demo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Network tab test")
        self.resize(1200, 700)
        self.setStyleSheet(stylesheet(LIGHT))

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tab = NetworkTab()
        layout.addWidget(self.tab, 1)

        btn = QPushButton("Load sample_cdr.csv → update network")
        btn.clicked.connect(self._load)
        layout.addWidget(btn)

        btn_clear = QPushButton("Clear → show empty state")
        btn_clear.clicked.connect(self.tab.clear)
        layout.addWidget(btn_clear)

    def _load(self):
        df = load_single_file("sample_cdr.csv")
        g = build_call_graph(df)
        cent = centrality_table(g)
        # Pass empty mutual for this test (Target B not loaded)
        mutual = mutual_contacts(df, df.iloc[0:0])
        self.tab.update_data(g, cent, mutual)


app = QApplication(sys.argv)
w = Demo()
w.show()
sys.exit(app.exec_())