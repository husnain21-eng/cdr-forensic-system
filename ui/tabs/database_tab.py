"""Database tab — audit trail viewer with full-chain verification."""
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
    """Audit trail viewer with HMAC chain verification."""

    def __init__(self, audit: AuditTrail, parent=None):
        super().__init__(parent)
        self._audit = audit

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()

        title = QLabel("Tamper-Evident Audit Trail Log")
        title.setStyleSheet("font-size: 16px; font-weight: 700;")

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet(
            "color: #6B7280; font-size: 12px;"
        )
        self.lbl_status.setWordWrap(True)

        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.clicked.connect(self.refresh)

        btn_verify = QPushButton("🔒 Verify Chain")
        btn_verify.setProperty("role", "primary")
        btn_verify.clicked.connect(self.verify_integrity)

        header.addWidget(title)
        header.addWidget(self.lbl_status, 1)
        header.addWidget(btn_refresh)
        header.addWidget(btn_verify)
        layout.addLayout(header)

        table_box = QGroupBox("Recorded Actions")
        table_layout = QVBoxLayout(table_box)
        self.tbl = DataTable()
        self.model = PandasModel()
        self.tbl.setModel(self.model)
        table_layout.addWidget(self.tbl)
        layout.addWidget(table_box, 1)

        self.refresh()

    # ---------- public API ----------

    def refresh(self) -> None:
        try:
            cols, rows = self._audit.fetch_all()
        except Exception as e:
            self.lbl_status.setText(
                f"<span style='color:#DC2626;'>Error: {e}</span>"
            )
            return

        if not rows:
            self.model.set_dataframe(
                pd.DataFrame({"Notice": ["No audit entries yet"]})
            )
            self.lbl_status.setText("No entries recorded yet.")
            return

        df = pd.DataFrame(rows, columns=cols)

        if "digital_signature" in df.columns:
            df["digital_signature"] = (
                df["digital_signature"].astype(str).str[:12] + "…"
            )
        if "previous_hash" in df.columns:
            df["previous_hash"] = (
                df["previous_hash"].astype(str).str[:10] + "…"
            )

        df = df.rename(columns={
            "id": "ID",
            "investigator": "Investigator",
            "role": "Role",
            "action_type": "Action",
            "details": "Details",
            "previous_hash": "Prev Hash",
            "digital_signature": "Signature",
            "timestamp": "Timestamp",
        })

        self.model.set_dataframe(df)
        self.lbl_status.setText(f"{len(df)} entries")
        self.lbl_status.setStyleSheet(
            "color: #6B7280; font-size: 12px;"
        )

    def verify_integrity(self) -> None:
        """Verify the entire hash chain."""
        try:
            valid, total = self._audit.verify_chain()
        except Exception as e:
            self.lbl_status.setText(
                f"<span style='color:#DC2626;'>Error: {e}</span>"
            )
            return

        if total == 0:
            self.lbl_status.setText("Nothing to verify.")
            return

        if valid == total:
            self.lbl_status.setStyleSheet(
                "color: #16A34A; font-size: 12px; font-weight: 600;"
            )
            self.lbl_status.setText(
                f"✅ Full chain verified — {valid}/{total} entries intact"
            )
        else:
            broken = total - valid
            self.lbl_status.setStyleSheet(
                "color: #DC2626; font-size: 12px; font-weight: 600;"
            )
            self.lbl_status.setText(
                f"⚠️ Chain integrity broken — {broken} invalid entries "
                f"detected ({valid}/{total} intact)"
            )