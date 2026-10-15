"""Dashboard tab — the landing page after login.

Displays:
  - Top interlocutors bar chart (matplotlib)
  - Risk assessment card
  - Anomaly summary card

This tab is dumb: it receives prepared data and displays it. All
analysis happens in the main window.
"""
from __future__ import annotations

import pandas as pd
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

        # Page 0 — Empty
        self.empty = EmptyState(
            icon="📊",
            title="No dashboard yet",
            hint="Load a CDR file to see risk scoring and top contacts.",
        )
        self.stack.addWidget(self.empty)

        # Page 1 — Content
        self.content = self._build_content()
        self.stack.addWidget(self.content)

        self.stack.setCurrentIndex(0)

    # ---------- UI ----------

    def _build_content(self) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Left: chart
        chart_box = QGroupBox("Top Interlocutors")
        chart_layout = QVBoxLayout(chart_box)
        self.canvas = FigureCanvasQTAgg(Figure(figsize=(5, 4), dpi=90))
        self.ax = self.canvas.figure.add_subplot(111)
        chart_layout.addWidget(self.canvas)
        layout.addWidget(chart_box, 3)

        # Right: risk + anomalies
        right = QVBoxLayout()
        right.setSpacing(16)

        # Risk card
        risk_box = QGroupBox("Risk Assessment")
        risk_layout = QVBoxLayout(risk_box)

        self.lbl_score = QLabel("—")
        self.lbl_score.setStyleSheet(
            "font-size: 28px; font-weight: 700; color: #374151;"
        )

        self.lbl_level = QLabel("—")
        self.lbl_level.setStyleSheet(
            "font-size: 13px; font-weight: 600; color: #6B7280;"
        )

        self.txt_rationale = QTextEdit()
        self.txt_rationale.setReadOnly(True)
        self.txt_rationale.setMaximumHeight(140)
        self.txt_rationale.setStyleSheet(
            "font-size: 12px; color: #4B5563;"
            "background: #F9FAFB;"
            "border: 1px solid #E5E7EB;"
            "border-radius: 6px;"
        )

        risk_layout.addWidget(self.lbl_score)
        risk_layout.addWidget(self.lbl_level)
        risk_layout.addWidget(self.txt_rationale)
        right.addWidget(risk_box)

        # Anomalies card
        anomalies_box = QGroupBox("Anomaly Summary")
        anomalies_layout = QVBoxLayout(anomalies_box)

        self.lbl_anomalies = QLabel("—")
        self.lbl_anomalies.setStyleSheet("font-size: 12px; color: #4B5563;")

        anomalies_layout.addWidget(self.lbl_anomalies)
        right.addWidget(anomalies_box)

        right.addStretch()

        right_widget = QWidget()
        right_widget.setLayout(right)
        layout.addWidget(right_widget, 2)

        return page

    # ---------- public API ----------

    def update_data(
        self,
        df: pd.DataFrame,
        risk: RiskAssessment,
        anomaly_summary: dict,
    ) -> None:
        """Refresh the dashboard with new data.

        Args:
            df: Normalized CDR DataFrame.
            risk: RiskAssessment from data.analyzer.risk.compute_risk.
            anomaly_summary: dict from data.analyzer.anomalies.summary.
        """
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
                self.ax.set_xlabel("Call count", fontsize=9)
                self.ax.tick_params(axis="y", labelsize=9)
                self.ax.tick_params(axis="x", labelsize=9)
                for spine in ("top", "right"):
                    self.ax.spines[spine].set_visible(False)
        self.canvas.figure.tight_layout()
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
            f"font-size: 13px; font-weight: 600; color: {color};"
        )
        self.lbl_score.setStyleSheet(
            f"font-size: 28px; font-weight: 700; color: {color};"
        )

        self.txt_rationale.setPlainText(risk.rationale)

        # --- Anomalies card ---
        total = anomaly_summary.get("total", 0)
        short = anomaly_summary.get("short_calls", 0)
        night = anomaly_summary.get("night_calls", 0)
        short_pct = anomaly_summary.get("short_pct", 0.0)
        night_pct = anomaly_summary.get("night_pct", 0.0)

        self.lbl_anomalies.setText(
            f"<b>Total records:</b> {total:,}<br>"
            f"<b>Short calls (≤5s):</b> {short:,} ({short_pct}%)<br>"
            f"<b>Night calls (23:00–05:00):</b> {night:,} ({night_pct}%)"
        )

        self.stack.setCurrentIndex(1)

    def clear(self) -> None:
        """Return to the empty state."""
        self.stack.setCurrentIndex(0)