"""Themed confirmation dialog for destructive or irreversible actions.

Usage:
    from ui.dialogs.confirm_dialog import confirm

    if confirm(self, "Reset session?", "All loaded data will be cleared."):
        do_reset()

    if confirm(self, "Delete target?", "Cannot be undone.", danger=True):
        do_delete()
"""
from __future__ import annotations

from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.theme.palette import LIGHT
from ui.theme.stylesheet import stylesheet


class ConfirmDialog(QDialog):
    """Themed yes/no dialog."""

    def __init__(
        self,
        parent: QWidget | None,
        title: str,
        message: str,
        *,
        danger: bool = False,
        confirm_word: str | None = None,
        ok_text: str | None = None,
        cancel_text: str = "Cancel",
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(420)
        self.setStyleSheet(stylesheet(LIGHT))

        self._confirm_word = confirm_word

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(12)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(
            "font-size: 17px; font-weight: 700;"
        )

        # Message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("color: #4B5563; font-size: 13px;")

        layout.addWidget(title_label)
        layout.addWidget(message_label)

        # Optional typed confirmation
        if confirm_word:
            hint = QLabel(
                f"Type <b>{confirm_word}</b> to confirm:"
            )
            hint.setStyleSheet("font-size: 12px; color: #6B7280;")
            layout.addWidget(hint)

            self.txt_confirm = QLineEdit()
            self.txt_confirm.setPlaceholderText(confirm_word)
            self.txt_confirm.textChanged.connect(self._update_ok_enabled)
            layout.addWidget(self.txt_confirm)
        else:
            self.txt_confirm = None

        layout.addSpacing(6)

        # Buttons
        buttons = QHBoxLayout()
        buttons.addStretch()

        cancel_btn = QPushButton(cancel_text)
        cancel_btn.clicked.connect(self.reject)

        ok_label = ok_text or ("Delete" if danger else "Confirm")
        ok_btn = QPushButton(ok_label)
        ok_btn.setProperty("role", "danger" if danger else "primary")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)

        if confirm_word:
            ok_btn.setEnabled(False)
            self._ok_btn = ok_btn

        buttons.addWidget(cancel_btn)
        buttons.addWidget(ok_btn)
        layout.addLayout(buttons)

    def _update_ok_enabled(self, text: str) -> None:
        """Enable OK only when the typed text matches confirm_word."""
        if not self._confirm_word:
            return
        self._ok_btn.setEnabled(text.strip() == self._confirm_word)


def confirm(
    parent: QWidget | None,
    title: str,
    message: str,
    *,
    danger: bool = False,
    confirm_word: str | None = None,
    ok_text: str | None = None,
    cancel_text: str = "Cancel",
) -> bool:
    """Show a themed confirmation dialog. Returns True if accepted."""
    dlg = ConfirmDialog(
        parent,
        title=title,
        message=message,
        danger=danger,
        confirm_word=confirm_word,
        ok_text=ok_text,
        cancel_text=cancel_text,
    )
    return dlg.exec_() == QDialog.Accepted