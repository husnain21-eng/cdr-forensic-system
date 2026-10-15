"""Temporary test for MainWindow workflow.

Exercises: loading, analysis pipeline, tabs, theme toggle, shortcuts.

Delete this file after verifying Phase 9.
"""
import sys
from pathlib import Path

from PyQt5.QtWidgets import QApplication

from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    # Fresh test database so audit trail starts clean
    test_db = Path("test_workflow.db")

    window = MainWindow(
        db_path=test_db,
        username="Husnain",
        role="Senior Investigator / Admin",
    )
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()