"""CDR Forensic System — application entry point."""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QDialog

from ui.dialogs.login_dialog import LoginDialog
from ui.main_window import MainWindow


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler("forensic_system.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def main() -> int:
    _setup_logging()
    log = logging.getLogger("main")
    log.info("Starting CDR Forensic System")

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setApplicationName("CDR Forensic System")

    db_path = Path("case_workspace.db")
    login = LoginDialog(db_path)
    if login.exec_() != QDialog.Accepted or not login.username:
        return 0

    window = MainWindow(
        db_path=db_path,
        username=login.username,
        role=login.role or "Junior Analyst",
    )
    app.installEventFilter(window)
    window.show()

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())