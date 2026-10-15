"""Temporary test for LoginDialog. Delete after verifying."""
import sys
from pathlib import Path

from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox

from ui.dialogs.login_dialog import LoginDialog


def main():
    app = QApplication(sys.argv)

    # Use a fresh test DB
    test_db = Path("test_login_workspace.db")

    dlg = LoginDialog(test_db)
    if dlg.exec_() == QDialog.Accepted:
        QMessageBox.information(
            None,
            "Login success",
            f"Username: {dlg.username}\nRole: {dlg.role}",
        )
    else:
        print("Dialog cancelled.")


if __name__ == "__main__":
    main()