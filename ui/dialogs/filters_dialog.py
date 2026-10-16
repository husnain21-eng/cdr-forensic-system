"""Advanced filter dialog with date/time range and phone number filter.

Returns the filter values via `get_values()` after the user clicks Apply.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from PyQt5.QtCore import QDateTime
from PyQt5.QtWidgets import (
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from ui.theme.palette import LIGHT
from ui.theme.stylesheet import stylesheet


class FiltersDialog(QDialog):
    """Modal dialog for date/time and phone-number filtering."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        default_from: datetime | None = None,
        default_to: datetime | None = None,
        default_phone: str = "",
    ):
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

        hint = QLabel(
            "Leave a field empty to skip that filter. "
            "Both date fields must be filled to filter by date range."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #6B7280; font-size: 11px;")
        layout.addWidget(hint)

        # Form
        form = QFormLayout()
        form.setSpacing(10)

        # Phone
        self.txt_phone = QLineEdit()
        self.txt_phone.setPlaceholderText("e.g. 923200569544 (contains match)")
        self.txt_phone.setText(default_phone)

        # Date/Time range
        default_from = default_from or (datetime.now() - timedelta(days=30))
        default_to = default_to or datetime.now()

        self.dt_from = QDateTimeEdit()
        self.dt_from.setCalendarPopup(True)
        self.dt_from.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.dt_from.setDateTime(QDateTime(default_from))

        self.dt_to = QDateTimeEdit()
        self.dt_to.setCalendarPopup(True)
        self.dt_to.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.dt_to.setDateTime(QDateTime(default_to))

        # Toggle: enable/disable date range
        from PyQt5.QtWidgets import QCheckBox
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

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Apply
            | QDialogButtonBox.Reset
            | QDialogButtonBox.Cancel
        )
        buttons.button(QDialogButtonBox.Apply).setText("Apply Filter")
        buttons.button(QDialogButtonBox.Reset).setText("Clear Filters")
        buttons.button(QDialogButtonBox.Cancel).setText("Cancel")

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.Reset).clicked.connect(self._clear)

        layout.addWidget(buttons)

    # ---------- helpers ----------

    def _toggle_date(self, enabled: bool) -> None:
        self.dt_from.setEnabled(enabled)
        self.dt_to.setEnabled(enabled)

    def _clear(self) -> None:
        self.txt_phone.clear()
        self.chk_date.setChecked(False)
        self.dt_from.setDateTime(
            QDateTime(datetime.now() - timedelta(days=30))
        )
        self.dt_to.setDateTime(QDateTime(datetime.now()))

    # ---------- public API ----------

    def get_values(self) -> dict:
        """Return the filter values as a dict."""
        return {
            "phone": self.txt_phone.text().strip(),
            "use_date": self.chk_date.isChecked(),
            "from": self.dt_from.dateTime().toPyDateTime(),
            "to": self.dt_to.dateTime().toPyDateTime(),
        }