"""Database tab — audit trail viewer with integrity verification.

Unlike other tabs, this one needs live access to the database. It
receives an AuditTrail instance in its constructor and calls
.fetch_all() to refresh the table.
"""
from __future__ import annotations

import pandas as pd
from PyQt5.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.audit import AuditTrail
from ui.components.data_table import DataTable
from ui.models.pandas_model import PandasModel


class DatabaseTab(QWidget):
    """Audit trail viewer with HMAC verification."""

    def __init__(self, audit: AuditTrail, parent=None):
        super().__init__(parent)
        self._audit = audit

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header row
        header = QHBoxLayout()

        title = QLabel("Tamper-Evident Audit Trail Log")
        title.setStyleSheet("font-size: 16px; font-weight: 700;")

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet(
            "color: #6B7280; font-size: 12px;"
        )

        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.clicked.connect(self.refresh)

        btn_verify = QPushButton("🔒 Verify Integrity")
        btn_verify.setProperty("role", "primary")
        btn_verify.clicked.connect(self.verify_integrity)

        header.addWidget(title)
        header.addWidget(self.lbl_status, 1)
        header.addWidget(btn_refresh)
        header.addWidget(btn_verify)
        layout.addLayout(header)

        # Audit table
        table_box = QGroupBox("Recorded Actions")
        table_layout = QVBoxLayout(table_box)
        self.tbl = DataTable()
        self.model = PandasModel()
        self.tbl.setModel(self.model)
        table_layout.addWidget(self.tbl)
        layout.addWidget(table_box, 1)

        # First load
        self.refresh()

    # ---------- public API ----------

    def refresh(self) -> None:
        """Reload the audit log from the database."""
        try:
            cols, rows = self._audit.fetch_all()
        except Exception as e:
            self.lbl_status.setText(f"<span style='color:#DC2626;'>Error: {e}</span>")
            return

        if not rows:
            self.model.set_dataframe(pd.DataFrame({"Notice": ["No audit entries yet"]}))
            self.lbl_status.setText("No entries recorded yet.")
            return

        df = pd.DataFrame(rows, columns=cols)

        # Truncate the signature for readability
        if "digital_signature" in df.columns:
            df["digital_signature"] = df["digital_signature"].astype(str).str[:12] + "…"

        # Rename for display
        df = df.rename(columns={
            "id": "ID",
            "investigator": "Investigator",
            "role": "Role",
            "action_type": "Action",
            "details": "Details",
            "digital_signature": "Signature",
            "timestamp": "Timestamp",
        })

        self.model.set_dataframe(df)
        self.lbl_status.setText(f"{len(df)} entries")
        self.lbl_status.setStyleSheet("color: #6B7280; font-size: 12px;")

    def verify_integrity(self) -> None:
        """Verify HMAC signatures for every audit row."""
        try:
            cols, rows = self._audit.fetch_all()
        except Exception as e:
            self.lbl_status.setText(f"<span style='color:#DC2626;'>Error: {e}</span>")
            return

        if not rows:
            self.lbl_status.setText("Nothing to verify.")
            return

        df = pd.DataFrame(rows, columns=cols)

        valid = 0
        invalid = 0
        for _, row in df.iterrows():
            try:
                ok = self._audit.verify_entry(
                    investigator=row["investigator"] or "",
                    role=row["role"] or "",
                    action_type=row["action_type"] or "",
                    details=row["details"] or "",
                    timestamp=row["timestamp"] or "",
                    signature=row["digital_signature"] or "",
                )
            except Exception:
                ok = False
            if ok:
                valid += 1
            else:
                invalid += 1

        if invalid == 0:
            self.lbl_status.setStyleSheet(
                "color: #16A34A; font-size: 12px; font-weight: 600;"
            )
            self.lbl_status.setText(f"✅ All {valid} entries verified (HMAC valid)")
        else:
            self.lbl_status.setStyleSheet(
                "color: #DC2626; font-size: 12px; font-weight: 600;"
            )
            self.lbl_status.setText(
                f"⚠️ {invalid} entries could not be verified, {valid} valid"
            )