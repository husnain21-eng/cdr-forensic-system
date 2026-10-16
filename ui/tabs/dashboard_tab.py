"""Dashboard tab — the landing page after login.

Layout (top → bottom):
  1. Top Interlocutors chart (full width)
  2. Risk Assessment + Anomaly Summary side by side

Vertical stacking means neither the chart nor the text cards get
squeezed horizontally at any font size.
"""
from __future__ import annotations

import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from data.analyzer.risk import RiskAssessment
from ui.components.empty_state import EmptyState


class DashboardTab(QWidget):
    """Two-page stack: empty state + real content."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        self.empty = EmptyState(
            icon="📊",
            title="No dashboard yet",
            hint="Load a CDR file to see risk scoring and top contacts.",
        )
        self.stack.addWidget(self.empty)

        self.content = self._build_content()
        self.stack.addWidget(self.content)

        self.stack.setCurrentIndex(0)

    # ---------- UI ----------

    def _build_content(self) -> QWidget:
        page = QWidget()
        page.setMinimumWidth(700)
        page.setMinimumHeight(560)

        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # --- TOP: chart (full width) ---
        chart_box = QGroupBox("Top Interlocutors")
        chart_layout = QVBoxLayout(chart_box)
        chart_layout.setContentsMargins(8, 8, 8, 8)

        self.canvas = FigureCanvasQTAgg(Figure(figsize=(9, 4), dpi=90))
        self.canvas.setMinimumHeight(340)
        self.ax = self.canvas.figure.add_subplot(111)
        chart_layout.addWidget(self.canvas)

        layout.addWidget(chart_box, 3)

        # --- BOTTOM: Risk + Anomalies side by side ---
        bottom = QHBoxLayout()
        bottom.setSpacing(12)

        # --- Risk card ---
        risk_box = QGroupBox("Risk Assessment")
        risk_box.setMinimumWidth(320)
        risk_layout = QVBoxLayout(risk_box)
        risk_layout.setContentsMargins(12, 16, 12, 12)
        risk_layout.setSpacing(6)

        self.lbl_score = QLabel("—")
        self.lbl_score.setStyleSheet(
            "font-size: 28px; font-weight: 700; color: #374151;"
        )
        self.lbl_score.setWordWrap(True)

        self.lbl_level = QLabel("—")
        self.lbl_level.setStyleSheet(
            "font-size: 14px; font-weight: 600; color: #6B7280;"
        )
        self.lbl_level.setWordWrap(True)

        self.txt_rationale = QTextEdit()
        self.txt_rationale.setReadOnly(True)
        self.txt_rationale.setMinimumHeight(120)
        self.txt_rationale.setStyleSheet(
            "font-size: 12px; color: #4B5563;"
            "background: #F9FAFB;"
            "border: 1px solid #E5E7EB;"
            "border-radius: 6px;"
        )

        risk_layout.addWidget(self.lbl_score)
        risk_layout.addWidget(self.lbl_level)
        risk_layout.addWidget(self.txt_rationale, 1)

        bottom.addWidget(risk_box, 1)

        # --- Anomaly card ---
        anom_box = QGroupBox("Anomaly Summary")
        anom_box.setMinimumWidth(320)
        anom_layout = QVBoxLayout(anom_box)
        anom_layout.setContentsMargins(12, 16, 12, 12)

        self.lbl_anomalies = QLabel("—")
        self.lbl_anomalies.setWordWrap(True)
        self.lbl_anomalies.setTextFormat(Qt.RichText)
        self.lbl_anomalies.setStyleSheet(
            "font-size: 13px; color: #374151;"
        )
        self.lbl_anomalies.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        anom_layout.addWidget(self.lbl_anomalies, 1)

        bottom.addWidget(anom_box, 1)

        layout.addLayout(bottom, 2)
        return page

    # ---------- public API ----------

    def update_data(
        self,
        df: pd.DataFrame,
        risk: RiskAssessment,
        anomaly_summary: dict,
    ) -> None:
        if df.empty:
            self.stack.setCurrentIndex(0)
            return

        # --- Chart ---
        self.ax.clear()
        if "party_b" in df.columns:
            top = (
                df["party_b"]
                .dropna()
                .astype(str)
                .value_counts()
                .head(8)
            )
            if not top.empty:
                self.ax.barh(top.index, top.values, color="#2563EB")
                self.ax.invert_yaxis()
                self.ax.set_xlabel("Call count", fontsize=10)
                self.ax.tick_params(axis="y", labelsize=10)
                self.ax.tick_params(axis="x", labelsize=10)
                for spine in ("top", "right"):
                    self.ax.spines[spine].set_visible(False)
                # Reserve 30% of the width for phone-number labels
                self.canvas.figure.subplots_adjust(
                    left=0.32, right=0.98, top=0.92, bottom=0.14
                )
        self.canvas.draw()

        # --- Risk card ---
        self.lbl_score.setText(f"{risk.score} / 100")

        level_colors = {
            "LOW": "#16A34A",
            "ELEVATED": "#D97706",
            "CRITICAL": "#DC2626",
            "UNKNOWN": "#6B7280",
        }
        color = level_colors.get(risk.level, "#6B7280")
        self.lbl_level.setText(f"● {risk.level}")
        self.lbl_level.setStyleSheet(
            f"font-size: 14px; font-weight: 600; color: {color};"
        )
        self.lbl_score.setStyleSheet(
            f"font-size: 28px; font-weight: 700; color: {color};"
        )

        self.txt_rationale.setPlainText(risk.rationale)

        # --- Anomaly card ---
        total = anomaly_summary.get("total", 0)
        short = anomaly_summary.get("short_calls", 0)
        night = anomaly_summary.get("night_calls", 0)
        short_pct = anomaly_summary.get("short_pct", 0.0)
        night_pct = anomaly_summary.get("night_pct", 0.0)

        self.lbl_anomalies.setText(
            f"<b>Total records:</b> {total:,}<br><br>"
            f"<b>Short calls (≤5s):</b><br>"
            f"{short:,} &nbsp;({short_pct}%)<br><br>"
            f"<b>Night calls (23:00–05:00):</b><br>"
            f"{night:,} &nbsp;({night_pct}%)"
        )

        self.stack.setCurrentIndex(1)

    def clear(self) -> None:
        self.stack.setCurrentIndex(0)