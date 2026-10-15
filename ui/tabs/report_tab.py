"""Report tab — PDF dossier preview and export.

Emits `export_pdf_requested` when the user clicks "Export PDF". The
main window handles the file dialog and generation.
"""
from __future__ import annotations

import pandas as pd
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from data.analyzer.risk import RiskAssessment
from ui.components.empty_state import EmptyState


class ReportTab(QWidget):
    """Two-page stack: empty state + report preview."""

    export_pdf_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        # Page 0 — Empty
        self.empty = EmptyState(
            icon="📄",
            title="No report yet",
            hint="Load a CDR file to generate a PDF dossier.",
        )
        self.stack.addWidget(self.empty)

        # Page 1 — Content
        self.content = self._build_content()
        self.stack.addWidget(self.content)

        self.stack.setCurrentIndex(0)

    # ---------- UI ----------

    def _build_content(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Risk card
        risk_box = QGroupBox("Risk Assessment (Documented Heuristic)")
        risk_layout = QVBoxLayout(risk_box)

        self.lbl_score = QLabel("—")
        self.lbl_score.setStyleSheet(
            "font-size: 24px; font-weight: 700; color: #374151;"
        )

        self.lbl_level = QLabel("—")
        self.lbl_level.setStyleSheet(
            "font-size: 13px; font-weight: 600; color: #6B7280;"
        )

        self.txt_rationale = QTextEdit()
        self.txt_rationale.setReadOnly(True)
        self.txt_rationale.setMaximumHeight(120)
        self.txt_rationale.setStyleSheet(
            "font-size: 12px; color: #4B5563;"
            "background: #F9FAFB;"
            "border: 1px solid #E5E7EB;"
            "border-radius: 6px;"
        )

        risk_layout.addWidget(self.lbl_score)
        risk_layout.addWidget(self.lbl_level)
        risk_layout.addWidget(self.txt_rationale)
        layout.addWidget(risk_box)

        # Preview of what will be in the PDF
        preview_box = QGroupBox("PDF Preview — Sections Included")
        preview_layout = QVBoxLayout(preview_box)

        self.lbl_preview = QLabel("—")
        self.lbl_preview.setStyleSheet("font-size: 12px; color: #4B5563;")
        self.lbl_preview.setWordWrap(True)
        preview_layout.addWidget(self.lbl_preview)

        layout.addWidget(preview_box)
        layout.addStretch()

        # Action row
        action_row = QHBoxLayout()
        action_row.addStretch()

        self.btn_export = QPushButton("📥  Export PDF Dossier")
        self.btn_export.setProperty("role", "primary")
        self.btn_export.setMinimumHeight(42)
        self.btn_export.clicked.connect(self.export_pdf_requested.emit)

        action_row.addWidget(self.btn_export)
        layout.addLayout(action_row)

        return page

    # ---------- public API ----------

    def update_data(
        self,
        df: pd.DataFrame,
        risk: RiskAssessment,
    ) -> None:
        """Refresh the preview.

        Args:
            df: Normalized CDR DataFrame.
            risk: RiskAssessment from data.analyzer.risk.compute_risk.
        """
        if df.empty:
            self.stack.setCurrentIndex(0)
            return

        # Risk card
        level_colors = {
            "LOW": "#16A34A",
            "ELEVATED": "#D97706",
            "CRITICAL": "#DC2626",
            "UNKNOWN": "#6B7280",
        }
        color = level_colors.get(risk.level, "#6B7280")

        self.lbl_score.setText(f"{risk.score} / 100")
        self.lbl_score.setStyleSheet(
            f"font-size: 24px; font-weight: 700; color: {color};"
        )

        self.lbl_level.setText(f"● {risk.level}")
        self.lbl_level.setStyleSheet(
            f"font-size: 13px; font-weight: 600; color: {color};"
        )

        self.txt_rationale.setPlainText(risk.rationale)

        # Preview
        top_count = 20
        if "party_b" in df.columns:
            top_count = min(top_count, df["party_b"].nunique())

        tower_count = 0
        if "cell_id" in df.columns:
            tower_count = min(20, df["cell_id"].nunique())

        self.lbl_preview.setText(
            f"The exported PDF will include:<br>"
            f"&nbsp;&nbsp;• Investigator info<br>"
            f"&nbsp;&nbsp;• Risk assessment with rationale<br>"
            f"&nbsp;&nbsp;• Dataset summary ({len(df):,} records)<br>"
            f"&nbsp;&nbsp;• Top {top_count} interlocutors table<br>"
            f"&nbsp;&nbsp;• {tower_count} cell towers/sites table<br>"
            f"&nbsp;&nbsp;• Watermark + confidentiality header on every page"
        )

        self.stack.setCurrentIndex(1)

    def clear(self) -> None:
        """Return to the empty state."""
        self.stack.setCurrentIndex(0)