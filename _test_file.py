"""Temporary test for the TopToolbar component. Delete after verifying."""
import sys

from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget

from ui.components.toolbar import TopToolbar
from ui.theme.palette import LIGHT
from ui.theme.stylesheet import stylesheet


class Demo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Toolbar test")
        self.resize(1100, 500)
        self.setStyleSheet(stylesheet(LIGHT))

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.toolbar = TopToolbar(username="Husnain", role="Admin")
        layout.addWidget(self.toolbar)

        # Log label — proves signals fire
        self.log = QLabel("  Click a button to see what signal fires...")
        self.log.setStyleSheet("padding: 20px; font-size: 14px;")
        layout.addWidget(self.log)
        layout.addStretch()

        # Wire each signal to the log
        self.toolbar.load_single.connect(lambda: self.log.setText("  📂 Open CDR clicked"))
        self.toolbar.load_bulk.connect(lambda: self.log.setText("  📂 Bulk clicked"))
        self.toolbar.load_target_b.connect(lambda: self.log.setText("  🎯 Target B clicked"))
        self.toolbar.toggle_theme.connect(lambda: self.log.setText("  ◐ Theme toggled"))
        self.toolbar.open_filters.connect(lambda: self.log.setText("  ⚙ Filters opened"))
        self.toolbar.search_changed.connect(
            lambda text: self.log.setText(f"  🔍 Search: '{text}'")
        )


app = QApplication(sys.argv)
w = Demo()
w.show()
sys.exit(app.exec_())