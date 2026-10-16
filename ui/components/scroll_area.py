"""A scrollable wrapper for tab pages."""
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QScrollArea, QWidget


class ScrollablePage(QScrollArea):
    """Wraps a widget so it scrolls if the window is too small."""

    def __init__(self, inner: QWidget, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setWidget(inner)