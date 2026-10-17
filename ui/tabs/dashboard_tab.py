"""Dashboard tab — the landing page after login."""
from __future__ import annotations

import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QGroupBox, QHBoxLayout, QLabel, QStackedWidget,
    QTextEdit, QVBoxLayout, QWidget,
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

    def _build_content(self) -> QWidget:
        page = QWidget()
        page.setMinimumWidth(800)
        page.setMinimumHeight(560)

        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # --- TOP: chart ---
        chart_box = QGroupBox("Top Interlocutors")
        chart_layout = QVBoxLayout(chart_box)
        self.canvas = FigureCanvasQTAgg(Figure(figsize=(9, 3.5), dpi=90))
        self.canvas.setMinimumHeight(280)
        self.ax = self.canvas.figure.add_subplot(111)
        chart_layout.addWidget(self.canvas)
        layout.addWidget(chart_box, 3)

        # --- BOTTOM: 3 Cards ---
        bottom = QHBoxLayout()
        bottom.setSpacing(12)

        # 1. Risk card
        risk_box = QGroupBox("Risk Assessment")
        risk_layout = QVBoxLayout(risk_box)
        self.lbl_score = QLabel("—")
        self.lbl_score.setStyleSheet("font-size: 26px; font-weight: 700; color: #374151;")
        self.lbl_level = QLabel("—")
        self.lbl_level.setStyleSheet("font-size: 14px; font-weight: 600; color: #6B7280;")
        self.txt_rationale = QTextEdit()
        self.txt_rationale.setReadOnly(True)
        self.txt_rationale.setStyleSheet("font-size: 11px; color: #4B5563; background: #F9FAFB;")
        risk_layout.addWidget(self.lbl_score)
        risk_layout.addWidget(self.lbl_level)
        risk_layout.addWidget(self.txt_rationale)
        bottom.addWidget(risk_box, 1)

        # 2. Anomaly card
        anom_box = QGroupBox("Anomaly Summary")
        anom_layout = QVBoxLayout(anom_box)
        self.lbl_anomalies = QLabel("—")
        self.lbl_anomalies.setWordWrap(True)
        self.lbl_anomalies.setStyleSheet("font-size: 13px; color: #374151;")
        anom_layout.addWidget(self.lbl_anomalies)
        bottom.addWidget(anom_box, 1)

        # 3. Markov Prediction card
        markov_box = QGroupBox("Markov Predictive Model (Next Call)")
        markov_layout = QVBoxLayout(markov_box)
        self.lbl_markov = QLabel("—")
        self.lbl_markov.setWordWrap(True)
        self.lbl_markov.setStyleSheet("font-size: 13px; color: #2563EB; font-weight: bold;")
        self.txt_markov_details = QTextEdit()
        self.txt_markov_details.setReadOnly(True)
        self.txt_markov_details.setStyleSheet("font-size: 11px; color: #4B5563; background: #F9FAFB;")
        markov_layout.addWidget(self.lbl_markov)
        markov_layout.addWidget(self.txt_markov_details)
        bottom.addWidget(markov_box, 1)

        layout.addLayout(bottom, 2)
        return page

    def update_data(
            self,
            df: pd.DataFrame,
            risk: RiskAssessment,
            anomaly_summary: dict,
            markov_df: pd.DataFrame | None = None,
    ) -> None:
        if df.empty:
            self.stack.setCurrentIndex(0)
            return

        # Chart
        self.ax.clear()
        if "party_b" in df.columns:
            top = df["party_b"].dropna().astype(str).value_counts().head(8)
            if not top.empty:
                self.ax.barh(top.index, top.values, color="#2563EB")
                self.ax.invert_yaxis()
                self.ax.tick_params(axis="both", labelsize=9)
                self.ax.spines["top"].set_visible(False)
                self.ax.spines["right"].set_visible(False)
                self.canvas.figure.subplots_adjust(left=0.30, right=0.98, top=0.92, bottom=0.15)
        self.canvas.draw()

        # Risk
        colors = {"LOW": "#16A34A", "ELEVATED": "#D97706", "CRITICAL": "#DC2626", "UNKNOWN": "#6B7280"}
        color = colors.get(risk.level, "#6B7280")
        self.lbl_score.setText(f"{risk.score} / 100")
        self.lbl_score.setStyleSheet(f"font-size: 26px; font-weight: 700; color: {color};")
        self.lbl_level.setText(f"● {risk.level}")
        self.lbl_level.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {color};")
        self.txt_rationale.setPlainText(risk.rationale)

        # Anomalies
        total = anomaly_summary.get("total", 0)
        self.lbl_anomalies.setText(
            f"<b>Total records:</b> {total:,}<br>"
            f"<b>Short calls:</b> {anomaly_summary.get('short_calls', 0):,}<br>"
            f"<b>Night calls:</b> {anomaly_summary.get('night_calls', 0):,}"
        )

        # Markov Prediction
        if markov_df is not None and not markov_df.empty:
            top_pred = markov_df.iloc[0]
            self.lbl_markov.setText(
                f"Next likely call: {top_pred['Predicted Next Call']} ({top_pred['Probability (%)']}%)")

            # Show top 3 in the text box
            last_target = top_pred["Target's Last Call"]
            details = f"Based on last call to: {last_target}\n\n"
            for _, row in markov_df.head(3).iterrows():
                details += f"➔ {row['Predicted Next Call']} ({row['Probability (%)']}% prob)\n"
            self.txt_markov_details.setPlainText(details)
        else:
            self.lbl_markov.setText("Not enough sequential data")
            self.txt_markov_details.setPlainText("Need more calls to build a transition matrix.")

        self.stack.setCurrentIndex(1)

    def clear(self) -> None:
        self.stack.setCurrentIndex(0)