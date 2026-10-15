"""Themed error dialog with optional traceback and copy-to-clipboard.

Usage:
    from ui.dialogs.error_dialog import show_error

    try:
        risky_operation()
    except Exception as e:
        show_error(self, "Load failed", "Could not parse the CDR file.", e)
"""
from __future__ import annotations

import traceback

from PyQt5.QtGui import QGuiApplication
from PyQt5.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ui.theme.palette import LIGHT
from ui.theme.stylesheet import stylesheet


class ErrorDialog(QDialog):
    """Display an error with a friendly message and optional traceback."""

    def __init__(
        self,
        parent: QWidget | None,
        title: str,
        message: str,
        exception: BaseException | None = None,
        details: str | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(520)
        self.setStyleSheet(stylesheet(LIGHT))

        # Build full detail text
        if details is None and exception is not None:
            details = "".join(
                traceback.format_exception(
                    type(exception), exception, exception.__traceback__
                )
            )
        self._details = details or ""

        self._build_ui(title, message)

    # ---------- UI ----------

    def _build_ui(self, title: str, message: str) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(12)

        # Header row: red icon + title
        header = QHBoxLayout()
        header.setSpacing(10)

        icon = QLabel("⚠")
        icon.setStyleSheet("font-size: 28px; color: #DC2626;")

        title_label = QLabel(title)
        title_label.setStyleSheet(
            "font-size: 17px; font-weight: 700; color: #111827;"
        )

        header.addWidget(icon)
        header.addWidget(title_label)
        header.addStretch()
        layout.addLayout(header)

        # Friendly message
        msg = QLabel(message)
        msg.setWordWrap(True)
        msg.setStyleSheet("color: #4B5563; font-size: 13px;")
        layout.addWidget(msg)

        # Collapsible details section
        if self._details:
            self.details_btn = QPushButton("▶  Show details")
            self.details_btn.setCheckable(True)
            self.details_btn.toggled.connect(self._toggle_details)
            layout.addWidget(self.details_btn)

            self.details_box = QTextEdit()
            self.details_box.setReadOnly(True)
            self.details_box.setPlainText(self._details)
            self.details_box.setStyleSheet(
                "font-family: 'Consolas', 'Courier New';"
                "font-size: 11px;"
                "background: #F9FAFB;"
                "border: 1px solid #E5E7EB;"
                "border-radius: 6px;"
                "color: #111827;"
            )
            self.details_box.setMinimumHeight(160)
            self.details_box.setVisible(False)
            layout.addWidget(self.details_box)

        layout.addSpacing(4)

        # Buttons
        buttons = QHBoxLayout()
        buttons.addStretch()

        if self._details:
            copy_btn = QPushButton("Copy details")
            copy_btn.clicked.connect(self._copy_details)
            buttons.addWidget(copy_btn)

        close_btn = QPushButton("Close")
        close_btn.setProperty("role", "primary")
        close_btn.setDefault(True)
        close_btn.clicked.connect(self.accept)
        buttons.addWidget(close_btn)

        layout.addLayout(buttons)

    # ---------- handlers ----------

    def _toggle_details(self, checked: bool) -> None:
        self.details_box.setVisible(checked)
        arrow = "▼" if checked else "▶"
        self.details_btn.setText(f"{arrow}  {'Hide details' if checked else 'Show details'}")
        self.adjustSize()

    def _copy_details(self) -> None:
        QGuiApplication.clipboard().setText(self._details)
        self.details_btn.setText("✓  Copied to clipboard")


def show_error(
    parent: QWidget | None,
    title: str,
    message: str,
    exception: BaseException | None = None,
    details: str | None = None,
) -> None:
    """Show a themed error dialog. Convenience wrapper."""
    dlg = ErrorDialog(parent, title, message, exception, details)
    dlg.exec_()