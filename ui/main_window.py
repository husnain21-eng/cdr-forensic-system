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
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.audit import AuditTrail
from core.database import Database
from data.analyzer.anomalies import night_calls, short_calls, summary
from data.analyzer.colocation import colocation_events
from data.analyzer.graph import build_call_graph, centrality_table
from data.analyzer.mutual import mutual_contacts
from data.analyzer.risk import compute_risk
from data.loader import load_single_file
from ui.components.sidebar import Sidebar
from ui.components.toolbar import TopToolbar
from ui.components.toast import toast
from ui.tabs.anomalies_tab import AnomaliesTab
from ui.tabs.dashboard_tab import DashboardTab
from ui.tabs.database_tab import DatabaseTab
from ui.tabs.inspector_tab import InspectorTab
from ui.tabs.map_tab import MapTab
from ui.tabs.network_tab import NetworkTab
from ui.tabs.report_tab import ReportTab

log = logging.getLogger(__name__)


# Sidebar items: (icon, label) — order matches the stack order
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

    # ============================================================
    # UI CONSTRUCTION
    # ============================================================

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

        # 5. Wire toolbar signals
        self._wire_toolbar()

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

    # ============================================================
    # TOOLBAR WIRING
    # ============================================================

    def _wire_toolbar(self) -> None:
        self.toolbar.load_single.connect(self._on_load_single)
        self.toolbar.load_bulk.connect(self._on_load_bulk)
        self.toolbar.load_target_b.connect(self._on_load_target_b)
        self.toolbar.search_changed.connect(self._on_search_changed)
        # Note: toggle_theme and open_filters are wired in Step 55

    # ============================================================
    # FILE LOADING
    # ============================================================

    def _on_load_single(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open CDR file",
            "",
            "CDR Files (*.csv *.xlsx *.xls);;All Files (*)",
        )
        if not path:
            return
        self._load_into_slot(path, target="A")

    def _on_load_bulk(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Open multiple CDR files",
            "",
            "CDR Files (*.csv *.xlsx *.xls);;All Files (*)",
        )
        if not paths:
            return
        self._load_bulk(paths)

    def _on_load_target_b(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Target B CDR",
            "",
            "CDR Files (*.csv *.xlsx *.xls);;All Files (*)",
        )
        if not path:
            return
        self._load_into_slot(path, target="B")

    def _load_into_slot(self, path: str, target: str) -> None:
        """Load a single file into slot A or B."""
        try:
            df = load_single_file(path)
        except Exception as e:
            log.exception("Load failed.")
            QMessageBox.critical(self, "Load failed", str(e))
            return

        if target == "A":
            self.df_a = df
        else:
            self.df_b = df

        label = f"Target {target}: {len(df):,} records"
        self.audit.log(
            self.current_user,
            self.current_role,
            f"LOAD_{target}",
            f"{label} from {path}",
        )
        toast(self, label + " loaded", tone="success")
        self.status_label.setText(label)
        self._refresh_all()

    def _load_bulk(self, paths: list[str]) -> None:
        """Load and concatenate multiple files into slot A."""
        frames = []
        errors = []
        for p in paths:
            try:
                frames.append(load_single_file(p))
            except Exception as e:
                errors.append(f"{p}: {e}")

        if not frames:
            QMessageBox.critical(
                self,
                "Bulk load failed",
                "None of the files could be loaded.\n\n" + "\n".join(errors),
            )
            return

        combined = pd.concat(frames, ignore_index=True)
        combined = combined.loc[:, ~combined.columns.duplicated()]
        combined.reset_index(drop=True, inplace=True)

        self.df_a = combined
        label = f"Bulk: {len(paths)} files, {len(combined):,} records"
        self.audit.log(
            self.current_user,
            self.current_role,
            "LOAD_BULK",
            label,
        )
        toast(self, label + " loaded", tone="success")
        self.status_label.setText(label)
        self._refresh_all()

    # ============================================================
    # SEARCH
    # ============================================================

    def _on_search_changed(self, text: str) -> None:
        """Live-filter the inspector tab."""
        if hasattr(self, "tab_inspector"):
            self.tab_inspector.txt_search.setText(text)

    # ============================================================
    # REFRESH PIPELINE
    # ============================================================

    def _refresh_all(self) -> None:
        """Compute every analysis and push results into tabs."""
        if self.df_a.empty:
            self.status_label.setText("No dataset loaded.")
            return

        df = self.df_a

        try:
            # Graph analysis
            g = build_call_graph(df)
            centrality = centrality_table(g)

            # Mutual contacts (only if Target B loaded)
            mutual = (
                mutual_contacts(df, self.df_b)
                if not self.df_b.empty
                else None
            )

            # Risk & anomalies
            risk = compute_risk(df)
            anom_summary = summary(df)
            short = short_calls(df)
            night = night_calls(df)

            # Co-location (only if both targets loaded)
            colocations = (
                colocation_events(df, self.df_b)
                if not self.df_b.empty
                else None
            )

            # Push to tabs
            self.tab_dashboard.update_data(df, risk, anom_summary)
            self.tab_network.update_data(g, centrality, mutual)
            self.tab_map.update_data(df)
            self.tab_anomalies.update_data(short, night, anom_summary)
            self.tab_report.update_data(df, risk)
            self.tab_inspector.update_data(df)
            self.tab_database.refresh()

            # Status
            self.status_label.setText(
                f"{len(df):,} records · Risk: {risk.score}/100 ({risk.level})"
            )

        except Exception as e:
            log.exception("Refresh pipeline failed.")
            QMessageBox.critical(self, "Analysis error", str(e))

    # ============================================================
    # LIFECYCLE
    # ============================================================

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