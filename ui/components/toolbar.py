"""Top toolbar with search, actions, and user badge.

Emits signals for each action. The main window connects them.
"""
from __future__ import annotations

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QToolButton,
)

from ui.theme.spacing import TOOLBAR_HEIGHT


class TopToolbar(QFrame):
    """Slim top bar with search and primary actions."""

    load_single = pyqtSignal()
    load_bulk = pyqtSignal()
    load_target_b = pyqtSignal()
    toggle_theme = pyqtSignal()
    open_filters = pyqtSignal()
    search_changed = pyqtSignal(str)

    def __init__(self, username: str, role: str, parent=None):
        super().__init__(parent)
        self.setObjectName("TopToolbar")
        self.setFixedHeight(TOOLBAR_HEIGHT)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(8)

        # Search
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search phone, tower, or case ID…")
        self.search.setClearButtonEnabled(True)
        self.search.setMinimumWidth(320)
        self.search.textChanged.connect(self.search_changed.emit)

        # Filters (opens drawer)
        btn_filters = QToolButton()
        btn_filters.setText("⚙  Filters")
        btn_filters.clicked.connect(self.open_filters.emit)

        # Primary action
        btn_single = QPushButton("📂  Open CDR")
        btn_single.setProperty("role", "primary")
        btn_single.clicked.connect(self.load_single.emit)

        # Secondary actions
        btn_bulk = QToolButton()
        btn_bulk.setText("Bulk")
        btn_bulk.clicked.connect(self.load_bulk.emit)

        btn_target_b = QToolButton()
        btn_target_b.setText("Target B")
        btn_target_b.clicked.connect(self.load_target_b.emit)

        # Theme toggle
        btn_theme = QToolButton()
        btn_theme.setText("◐")
        btn_theme.setToolTip("Toggle light / dark theme")
        btn_theme.clicked.connect(self.toggle_theme.emit)

        # User badge
        user_label = QLabel(f"<b>{username}</b> · {role}")
        user_label.setStyleSheet("padding: 0 8px;")

        layout.addWidget(self.search)
        layout.addStretch()
        layout.addWidget(btn_filters)
        layout.addWidget(btn_single)
        layout.addWidget(btn_bulk)
        layout.addWidget(btn_target_b)
        layout.addWidget(btn_theme)
        layout.addWidget(user_label)