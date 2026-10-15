"""Temporary test for the EmptyState component. Delete after verifying."""
import sys

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QStackedWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.components.empty_state import EmptyState
from ui.theme.palette import LIGHT
from ui.theme.stylesheet import stylesheet


class Demo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EmptyState test")
        self.resize(700, 400)
        self.setStyleSheet(stylesheet(LIGHT))

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.stack = QStackedWidget()

        # Page 0 — empty state
        empty = EmptyState(
            icon="📊",
            title="No CDR loaded",
            hint="Click 'Open CDR' to get started.",
        )
        self.stack.addWidget(empty)

        # Page 1 — "data" placeholder
        loaded = QWidget()
        vl = QVBoxLayout(loaded)
        from PyQt5.QtWidgets import QLabel
        vl.addWidget(QLabel("<h2>Data is here now!</h2>"))
        self.stack.addWidget(loaded)

        layout.addWidget(self.stack)

        btn = QPushButton("Toggle empty / loaded")
        btn.clicked.connect(self._toggle)
        layout.addWidget(btn)

    def _toggle(self):
        i = self.stack.currentIndex()
        self.stack.setCurrentIndex(0 if i == 1 else 1)


app = QApplication(sys.argv)
w = Demo()
w.show()
sys.exit(app.exec_())