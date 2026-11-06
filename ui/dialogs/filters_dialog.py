"""Advanced filter dialog with forced Apply logic."""
from __future__ import annotations

from datetime import datetime, timedelta

from PyQt5.QtCore import QDateTime
from PyQt5.QtWidgets import (
    QCheckBox, QDateTimeEdit, QDialog, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget,
)

from ui.theme.palette import LIGHT
from ui.theme.stylesheet import stylesheet


class FiltersDialog(QDialog):
    """Modal dialog for date/time and phone-number filtering."""

    def __init__(self, parent: QWidget | None = None, *, default_from=None, default_to=None, default_phone: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Advanced Filter")
        self.setModal(True)
        self.setMinimumWidth(440)
        self.setStyleSheet(stylesheet(LIGHT))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        heading = QLabel("<b>Filter Records</b>")
        heading.setStyleSheet("font-size: 15px;")
        layout.addWidget(heading)

        form = QFormLayout()
        form.setSpacing(10)

        self.txt_phone = QLineEdit()
        self.txt_phone.setPlaceholderText("e.g. 923200569544")
        self.txt_phone.setText(default_phone)

        default_from = default_from if default_from else (datetime.now() - timedelta(days=30))
        default_to = default_to if default_to else datetime.now()

        self.dt_from = QDateTimeEdit()
        self.dt_from.setCalendarPopup(True)
        self.dt_from.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.dt_from.setDateTime(QDateTime(default_from))

        self.dt_to = QDateTimeEdit()
        self.dt_to.setCalendarPopup(True)
        self.dt_to.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.dt_to.setDateTime(QDateTime(default_to))

        self.chk_date = QCheckBox("Filter by date range")
        self.chk_date.setChecked(False)
        self.chk_date.toggled.connect(self._toggle_date)
        self._toggle_date(False)

        form.addRow("Phone contains:", self.txt_phone)
        form.addRow(self.chk_date)
        form.addRow("From:", self.dt_from)
        form.addRow("To:", self.dt_to)

        layout.addLayout(form)
        layout.addStretch()

        # --- CUSTOM BUTTONS ---
        btn_layout = QHBoxLayout()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_clear = QPushButton("Clear Filters")
        btn_clear.clicked.connect(self._clear_and_accept)

        btn_apply = QPushButton("Apply Filter")
        btn_apply.setStyleSheet("background-color: #2563EB; color: white; font-weight: bold; padding: 8px 16px;")
        btn_apply.clicked.connect(self.accept)  # Forces the dialog to return code 1

        btn_layout.addWidget(btn_clear)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_apply)

        layout.addLayout(btn_layout)

    def _toggle_date(self, enabled: bool) -> None:
        self.dt_from.setEnabled(enabled)
        self.dt_to.setEnabled(enabled)

    def _clear_and_accept(self) -> None:
        self.txt_phone.clear()
        self.chk_date.setChecked(False)
        self.accept()

    def get_values(self) -> dict:
        return {
            "phone": self.txt_phone.text().strip(),
            "use_date": self.chk_date.isChecked(),
            "from": self.dt_from.dateTime().toString("yyyy-MM-dd HH:mm:ss"),
            "to": self.dt_to.dateTime().toString("yyyy-MM-dd HH:mm:ss"),
        }