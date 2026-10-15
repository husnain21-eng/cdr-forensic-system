"""Left sidebar navigation.

Emits `changed(index)` when the user selects a different item.
Connect that signal to a QStackedWidget to switch pages.
"""
from __future__ import annotations

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QButtonGroup,
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from ui.theme.spacing import SIDEBAR_WIDTH


class Sidebar(QFrame):
    """Vertical navigation bar with icon + label items."""

    changed = pyqtSignal(int)

    def __init__(
        self,
        items: list[tuple[str, str]],
        brand: str = "◈  CDR Forensics",
        parent=None,
    ):
        """items: list of (icon, label) tuples, e.g. [("◉", "Dashboard")]."""
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(SIDEBAR_WIDTH)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 18, 12, 12)
        layout.setSpacing(4)

        # Brand
        brand_label = QLabel(brand)
        brand_label.setStyleSheet(
            "font-size: 15px; font-weight: 700; padding: 6px 8px 16px 8px;"
        )
        layout.addWidget(brand_label)

        # Nav buttons
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        for i, (icon, label) in enumerate(items):
            btn = QPushButton(f"{icon}   {label}")
            btn.setObjectName("NavItem")
            btn.setCheckable(True)
            if i == 0:
                btn.setChecked(True)
            self._group.addButton(btn, i)
            layout.addWidget(btn)

        layout.addStretch()

        # Emit `changed` on click
        self._group.idClicked.connect(self.changed.emit)

    def set_current(self, index: int) -> None:
        """Programmatically select an item (no signal emitted)."""
        btn = self._group.button(index)
        if btn is not None:
            btn.setChecked(True)