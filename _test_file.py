"""Temporary test for ErrorDialog. Delete after verifying."""
import sys

from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget

from ui.dialogs.error_dialog import show_error
from ui.theme.palette import LIGHT
from ui.theme.stylesheet import stylesheet


class Demo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Error dialog test")
        self.resize(600, 400)
        self.setStyleSheet(stylesheet(LIGHT))

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(8)

        layout.addWidget(QLabel("  Click a button to see the error dialog:"))

        # Test 1: Simple error with no traceback
        b1 = QPushButton("Test 1: Simple message")
        b1.clicked.connect(lambda: show_error(
            self,
            "Load failed",
            "The CDR file could not be parsed.",
        ))

        # Test 2: Real exception with traceback
        def raise_something():
            try:
                _ = 1 / 0
            except ZeroDivisionError as e:
                show_error(
                    self,
                    "Calculation error",
                    "An unexpected error occurred during analysis.",
                    exception=e,
                )

        b2 = QPushButton("Test 2: Exception with traceback")
        b2.clicked.connect(raise_something)

        # Test 3: Custom details
        b3 = QPushButton("Test 3: Custom long details")
        b3.clicked.connect(lambda: show_error(
            self,
            "Import failure",
            "The import could not complete.",
            details=(
                "Row 42: missing 'party_b' column\n"
                "Row 58: invalid timestamp format\n"
                "Row 103: empty caller field\n" * 5
            ),
        ))

        layout.addWidget(b1)
        layout.addWidget(b2)
        layout.addWidget(b3)
        layout.addStretch()


app = QApplication(sys.argv)
w = Demo()
w.show()
sys.exit(app.exec_())