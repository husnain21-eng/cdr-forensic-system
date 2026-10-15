"""Friendly empty-state widget for tables and panels.

Shows an icon, a title, and a hint when there's nothing to display.
"""
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget


class EmptyState(QWidget):
    """A centered message with an icon, title, and hint."""

    def __init__(
        self,
        icon: str = "📭",
        title: str = "Nothing here yet",
        hint: str = "Load data to get started.",
        parent=None,
    ):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(6)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 56px;")
        icon_label.setAlignment(Qt.AlignCenter)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            "font-size: 16px; font-weight: 600; color: #374151;"
        )
        title_label.setAlignment(Qt.AlignCenter)

        hint_label = QLabel(hint)
        hint_label.setStyleSheet("color: #9CA3AF; font-size: 13px;")
        hint_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(hint_label)