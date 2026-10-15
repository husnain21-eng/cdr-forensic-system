"""Temporary test for MainWindow. Delete after verifying."""
import sys
from pathlib import Path

from PyQt5.QtWidgets import QApplication

from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    w = MainWindow(
        db_path=Path("test_main_workspace.db"),
        username="Husnain",
        role="Senior Investigator / Admin",
    )
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()