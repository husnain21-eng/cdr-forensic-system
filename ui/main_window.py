"""Main application window — wires everything together.

The window is the only component that:
  - Holds a Database and AuditTrail
  - Holds the currently loaded DataFrames (df_a, df_b)
  - Calls analyzers and pushes results into tabs
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.audit import AuditTrail
from core.database import Database
from ui.components.sidebar import Sidebar
from ui.components.toolbar import TopToolbar
from ui.tabs.anomalies_tab import AnomaliesTab
from ui.tabs.dashboard_tab import DashboardTab
from ui.tabs.database_tab import DatabaseTab
from ui.tabs.inspector_tab import InspectorTab
from ui.tabs.map_tab import MapTab
from ui.tabs.network_tab import NetworkTab
from ui.tabs.report_tab import ReportTab

log = logging.getLogger(__name__)


# Sidebar items: (icon, label)  — order matches the stack order
NAV_ITEMS = [
    ("◉", "Dashboard"),
    ("⬡", "Network"),
    ("◐", "Geo Map"),
    ("⚠", "Anomalies"),
    ("▤", "Database"),
    ("⎙", "Reports"),
    ("≣", "Raw Logs"),
]


class MainWindow(QMainWindow):
    """Top-level window."""

    def __init__(self, db_path: str | Path, username: str, role: str):
        super().__init__()
        self.db_path = Path(db_path)
        self.current_user = username
        self.current_role = role

        # Backend
        self.db = Database(self.db_path)
        self.db.open()
        self.audit = AuditTrail(self.db)

        # Session state
        self.df_a = pd.DataFrame()
        self.df_b = pd.DataFrame()

        # Build UI
        self._build_ui()

        # Log the session start
        self.audit.log(
            self.current_user,
            self.current_role,
            "LOGIN",
            "Session started.",
        )

    # ---------- UI construction ----------

    def _build_ui(self) -> None:
        self.setWindowTitle(
            f"CDR Forensic System — {self.current_user} "
            f"[{self.current_role}]"
        )
        self.resize(1400, 880)

        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 1. Toolbar
        self.toolbar = TopToolbar(
            username=self.current_user,
            role=self.current_role,
        )
        root.addWidget(self.toolbar)

        # 2. Sidebar + content stack
        middle = QHBoxLayout()
        middle.setContentsMargins(0, 0, 0, 0)
        middle.setSpacing(0)

        self.sidebar = Sidebar(NAV_ITEMS)
        middle.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self._build_tabs()
        middle.addWidget(self.stack, 1)

        root.addLayout(middle, 1)

        # 3. Status bar
        self._build_status_bar()

        # 4. Wire sidebar → stack
        self.sidebar.changed.connect(self.stack.setCurrentIndex)

    def _build_tabs(self) -> None:
        """Instantiate every tab and add it to the stack."""
        self.tab_dashboard = DashboardTab()
        self.tab_network = NetworkTab()
        self.tab_map = MapTab()
        self.tab_anomalies = AnomaliesTab()
        self.tab_database = DatabaseTab(self.audit)
        self.tab_report = ReportTab()
        self.tab_inspector = InspectorTab()

        # Order MUST match NAV_ITEMS
        self.stack.addWidget(self.tab_dashboard)
        self.stack.addWidget(self.tab_network)
        self.stack.addWidget(self.tab_map)
        self.stack.addWidget(self.tab_anomalies)
        self.stack.addWidget(self.tab_database)
        self.stack.addWidget(self.tab_report)
        self.stack.addWidget(self.tab_inspector)

    def _build_status_bar(self) -> None:
        sb = self.statusBar()

        self.status_label = QLabel("Ready.")
        self.user_label = QLabel(
            f"◉  {self.current_user} · {self.current_role}"
        )
        self.lock_label = QLabel("")
        self.lock_label.setStyleSheet("color: #6B7280;")

        sb.addWidget(self.status_label, 1)
        sb.addPermanentWidget(self.user_label)
        sb.addPermanentWidget(self.lock_label)

    # ---------- lifecycle ----------

    def closeEvent(self, event) -> None:
        try:
            self.audit.log(
                self.current_user,
                self.current_role,
                "LOGOUT",
                "Session ended.",
            )
        except Exception:
            log.exception("Audit on close failed.")

        try:
            self.db.close()
        except Exception:
            log.exception("DB close failed.")

        super().closeEvent(event)