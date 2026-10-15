"""Non-blocking toast notifications.

Usage:
    from ui.components.toast import toast
    toast(self, "Loaded 12,483 records", tone="success")
"""
from __future__ import annotations

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget


# Tone → dot color
_TONE_COLORS = {
    "info": "#2563EB",
    "success": "#16A34A",
    "warning": "#D97706",
    "error": "#DC2626",
}


class Toast(QFrame):
    """A floating, auto-dismissing notification."""

    MARGIN_FROM_EDGE = 24

    def __init__(
        self,
        parent: QWidget,
        message: str,
        tone: str = "info",
        duration_ms: int = 3000,
    ):
        super().__init__(parent)
        self.setObjectName("Toast")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(
            "#Toast {"
            "  background: #111827;"
            "  border-radius: 12px;"
            "}"
        )

        dot_color = _TONE_COLORS.get(tone, _TONE_COLORS["info"])

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        dot = QLabel("●")
        dot.setStyleSheet(f"color: {dot_color}; font-size: 14px;")

        text = QLabel(message)
        text.setStyleSheet("color: white; font-weight: 500;")

        layout.addWidget(dot)
        layout.addWidget(text)

        self.adjustSize()
        self._reposition()

        # Auto-dismiss
        QTimer.singleShot(duration_ms, self._dismiss)

    def _reposition(self) -> None:
        parent = self.parentWidget()
        if not parent:
            return
        x = parent.width() - self.width() - self.MARGIN_FROM_EDGE
        y = self.MARGIN_FROM_EDGE
        self.move(max(0, x), y)

    def _dismiss(self) -> None:
        self.hide()
        self.deleteLater()


def toast(
    parent: QWidget,
    message: str,
    tone: str = "info",
    duration_ms: int = 3000,
) -> None:
    """Convenience function: show a toast on the given parent widget."""
    Toast(parent, message, tone=tone, duration_ms=duration_ms)