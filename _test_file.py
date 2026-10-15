"""Temporary test for ConfirmDialog. Delete after verifying."""
import sys

from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget

from ui.dialogs.confirm_dialog import confirm
from ui.theme.palette import LIGHT
from ui.theme.stylesheet import stylesheet


class Demo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Confirm dialog test")
        self.resize(600, 400)
        self.setStyleSheet(stylesheet(LIGHT))

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(8)

        self.log = QLabel("  Click a button...")
        self.log.setStyleSheet("padding: 12px; font-size: 14px;")

        # Test 1: Simple info confirm
        b1 = QPushButton("Test 1: Info confirm")
        b1.clicked.connect(lambda: self._log(
            confirm(
                self,
                "Reset session?",
                "All loaded CDR data will be cleared.",
                ok_text="Reset",
            )
        ))

        # Test 2: Danger confirm
        b2 = QPushButton("Test 2: Danger confirm")
        b2.clicked.connect(lambda: self._log(
            confirm(
                self,
                "Delete target?",
                "This action cannot be undone.",
                danger=True,
            )
        ))

        # Test 3: Typed confirmation
        b3 = QPushButton("Test 3: Typed confirmation (type DELETE)")
        b3.clicked.connect(lambda: self._log(
            confirm(
                self,
                "Permanent delete",
                "Type DELETE to remove all records from the database.",
                danger=True,
                confirm_word="DELETE",
            )
        ))

        layout.addWidget(self.log)
        layout.addWidget(b1)
        layout.addWidget(b2)
        layout.addWidget(b3)
        layout.addStretch()

    def _log(self, result: bool):
        self.log.setText(f"  Result: {'✅ Accepted' if result else '❌ Cancelled'}")


app = QApplication(sys.argv)
w = Demo()
w.show()
sys.exit(app.exec_())