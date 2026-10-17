"""Main application window — wires everything together."""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from PyQt5.QtCore import QEvent, QTimer, Qt
from PyQt5.QtGui import QKeySequence, QCursor
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QGroupBox,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QShortcut,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core import settings as user_settings
from core.audit import AuditTrail
from core.constants import IDLE_TIMEOUT_SECONDS
from core.database import Database
from core.settings import MAX_FONT_SIZE, MIN_FONT_SIZE

# --- Data Analyzers ---
from data.analyzer.anomalies import night_calls, short_calls, summary, statistical_anomalies
from data.analyzer.colocation import colocation_events
from data.analyzer.graph import build_call_graph, centrality_table, detect_communities
from data.analyzer.markov import predict_next_call
from data.analyzer.mutual import mutual_contacts
from data.analyzer.risk import compute_risk

from data.loader import load_single_file
from maps.folium_builder import build_map as build_folium_map

# --- UI Components ---
from ui.components.data_table import DataTable
from ui.components.print_helper import print_widget
from ui.components.toolbar import TopToolbar
from ui.components.toast import toast
from ui.dialogs.confirm_dialog import confirm
from ui.dialogs.filters_dialog import FiltersDialog
from ui.tabs.anomalies_tab import AnomaliesTab
from ui.tabs.dashboard_tab import DashboardTab
from ui.tabs.database_tab import DatabaseTab
from ui.tabs.inspector_tab import InspectorTab
from ui.tabs.map_tab import MapTab
from ui.tabs.network_tab import NetworkTab
from ui.tabs.report_tab import ReportTab
from ui.theme.palette import DARK, LIGHT
from ui.theme.stylesheet import stylesheet

log = logging.getLogger(__name__)

TAB_ITEMS = [
    "◉  Dashboard",
    "⬡  Network",
    "◐  Geo Map",
    "⚠  Anomalies",
    "▤  Database",
    "⎙  Reports",
    "≣  Raw Logs",
]


class MainWindow(QMainWindow):
    """Top-level window."""

    def __init__(self, db_path, username, role):
        super().__init__()
        self.db_path = Path(db_path)
        self.current_user = username
        self.current_role = role

        self.db = Database(self.db_path)
        self.db.open()
        self.audit = AuditTrail(self.db)

        # Full dataset (unfiltered) and filtered view
        self.df_raw_a = pd.DataFrame()
        self.df_raw_b = pd.DataFrame()
        self.df_a = pd.DataFrame()
        self.df_b = pd.DataFrame()

        # Active filter state
        self._filter_state: dict = {
            "phone": "",
            "use_date": False,
            "from": None,
            "to": None,
        }

        self._theme_is_dark = False
        self._idle_seconds = 0
        self._font_size = user_settings.get("font_size", 14)

        self._build_ui()
        self._auto_size_to_screen()

        self.audit.log(
            self.current_user, self.current_role,
            "LOGIN", "Session started.",
        )
        self._install_idle_watch()
        self._install_shortcuts()

    # ============================================================
    # SCREEN AUTO-SIZING
    # ============================================================

    def _auto_size_to_screen(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            self.resize(1400, 880)
            return
        available = screen.availableGeometry()
        target_w = min(int(available.width() * 0.92), 1600)
        target_h = min(int(available.height() * 0.92), 1000)
        min_w = min(1000, int(available.width() * 0.80))
        min_h = min(640, int(available.height() * 0.80))
        self.setMinimumSize(min_w, min_h)
        self.resize(target_w, target_h)
        x = available.x() + (available.width() - target_w) // 2
        y = available.y() + (available.height() - target_h) // 2
        self.move(x, y)

    # ============================================================
    # UI CONSTRUCTION
    # ============================================================

    def _build_ui(self) -> None:
        self.setWindowTitle(
            f"CDR Forensic System — {self.current_user} [{self.current_role}]"
        )
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.toolbar = TopToolbar(
            username=self.current_user,
            role=self.current_role,
        )
        root.addWidget(self.toolbar)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self._build_tabs()
        root.addWidget(self.tabs, 1)

        self._install_print_corner_button()
        self._build_status_bar()
        self._wire_toolbar()
        self._apply_theme()

        # This activates the right-click printing feature
        self._install_section_printing()

    def _install_print_corner_button(self) -> None:
        self.print_btn = QPushButton("🖨  Print Tab")
        self.print_btn.setToolTip("Print the current tab (Ctrl+P)")
        self.print_btn.setMinimumHeight(28)
        self.print_btn.setStyleSheet(
            "QPushButton { padding: 4px 12px; font-size: 12px; }"
        )
        self.print_btn.clicked.connect(self._on_print_current_tab)
        self.tabs.setCornerWidget(self.print_btn, Qt.TopRightCorner)

    def _build_tabs(self) -> None:
        self.tab_dashboard = DashboardTab()
        self.tab_network = NetworkTab()
        self.tab_map = MapTab()
        self.tab_anomalies = AnomaliesTab()
        self.tab_database = DatabaseTab(self.audit)
        self.tab_report = ReportTab()
        self.tab_inspector = InspectorTab()

        for label, tab in zip(TAB_ITEMS, [
            self.tab_dashboard, self.tab_network, self.tab_map,
            self.tab_anomalies, self.tab_database, self.tab_report,
            self.tab_inspector,
        ]):
            self.tabs.addTab(self._scrollable(tab), label)

        self.tab_map.launch_map_requested.connect(self._on_launch_map)
        self.tab_report.export_pdf_requested.connect(self._on_export_pdf)

    def _scrollable(self, inner: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setWidget(inner)
        return scroll

    def _build_status_bar(self) -> None:
        sb = self.statusBar()
        self.status_label = QLabel("Ready.")

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(220)
        self.progress_bar.setMaximumHeight(16)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setVisible(False)

        self.user_label = QLabel(
            f"◉  {self.current_user} · {self.current_role}"
        )
        self.lock_label = QLabel("")
        self.lock_label.setStyleSheet("color: #6B7280;")

        sb.addWidget(self.status_label, 1)
        sb.addPermanentWidget(self.progress_bar)
        sb.addPermanentWidget(self.user_label)
        sb.addPermanentWidget(self.lock_label)

    # ============================================================
    # PRINTING (Full Tab + Specific Sections)
    # ============================================================

    def _on_print_current_tab(self) -> None:
        current = self.tabs.currentWidget()
        if current is None:
            return
        tab_name = self.tabs.tabText(self.tabs.currentIndex()).strip()
        try:
            printed = print_widget(current, parent=self, landscape=True)
            if not printed:
                return
            self.audit.log(
                self.current_user, self.current_role,
                "PRINT_TAB", f"Printed tab: {tab_name}",
            )
            toast(self, f"Sent '{tab_name}' to printer", tone="success")
            self.status_label.setText(f"Printed: {tab_name}")
        except Exception as e:
            log.exception("Print failed.")
            QMessageBox.critical(self, "Print error", str(e))

    def _install_section_printing(self) -> None:
        """Attach a right-click print menu to all GroupBoxes and Tables."""
        for group_box in self.findChildren(QGroupBox):
            group_box.setContextMenuPolicy(Qt.CustomContextMenu)
            group_box.customContextMenuRequested.connect(
                lambda pos, w=group_box: self._show_print_menu(pos, w)
            )
            group_box.setToolTip("Right-click to print this section")

        for table in self.findChildren(DataTable):
            table.setContextMenuPolicy(Qt.CustomContextMenu)
            table.customContextMenuRequested.connect(
                lambda pos, w=table: self._show_print_menu(pos, w)
            )
            table.setToolTip("Right-click to print this table")

    def _show_print_menu(self, pos, widget: QWidget) -> None:
        """Show the right-click context menu."""
        menu = QMenu(self)
        print_action = menu.addAction("🖨 Print this Section")
        action = menu.exec_(widget.mapToGlobal(pos))

        if action == print_action:
            self._on_print_section(widget)

    def _print_under_cursor(self) -> None:
        """Print whatever section the mouse is currently hovering over."""
        widget = QApplication.widgetAt(QCursor.pos())
        while widget is not None:
            if isinstance(widget, (QGroupBox, DataTable)):
                self._on_print_section(widget)
                return
            widget = widget.parentWidget()

    def _on_print_section(self, widget: QWidget) -> None:
        """Print a specific widget (sub-section)."""
        try:
            printed = print_widget(widget, parent=self, landscape=True)
            if printed:
                toast(self, "Section sent to printer", tone="success")
                self.status_label.setText("Section printed.")
        except Exception as e:
            log.exception("Section print failed.")
            QMessageBox.critical(self, "Print error", str(e))

    # ============================================================
    # FILTERS
    # ============================================================

    def _on_open_filters(self) -> None:
        dlg = FiltersDialog(
            self,
            default_from=self._filter_state.get("from"),
            default_to=self._filter_state.get("to"),
            default_phone=self._filter_state.get("phone", ""),
        )
        if dlg.exec_() != FiltersDialog.Accepted:
            return

        values = dlg.get_values()
        self._filter_state = values
        self._apply_filter()

        self.audit.log(
            self.current_user, self.current_role,
            "APPLY_FILTER",
            f"phone='{values['phone']}', date_range={values['use_date']}",
        )

    def _apply_filter(self) -> None:
        if self.df_raw_a.empty:
            toast(self, "No data to filter", tone="warning")
            return

        df = self.df_raw_a.copy()
        state = self._filter_state

        phone = state.get("phone", "")
        if phone:
            df = df[
                df["party_a"].astype(str).str.contains(phone, na=False)
                | df["party_b"].astype(str).str.contains(phone, na=False)
                ]

        if state.get("use_date") and "timestamp" in df.columns:
            dt_from = state.get("from")
            dt_to = state.get("to")
            if dt_from is not None and dt_to is not None:
                df = df[
                    (df["timestamp"] >= pd.Timestamp(dt_from))
                    & (df["timestamp"] <= pd.Timestamp(dt_to))
                    ]

        self.df_a = df.reset_index(drop=True)
        self._refresh_all()

        if len(self.df_a) < len(self.df_raw_a):
            self.status_label.setText(
                f"Filtered: {len(self.df_a):,} of {len(self.df_raw_a):,} records"
            )
            toast(self, f"Filtered to {len(self.df_a):,} records", tone="info")
        else:
            self.status_label.setText(f"{len(self.df_a):,} records (no filter applied)")

    def _clear_filter(self) -> None:
        self._filter_state = {"phone": "", "use_date": False, "from": None, "to": None}
        self.df_a = self.df_raw_a.copy()
        self._refresh_all()
        toast(self, "Filters cleared", tone="info")

    # ============================================================
    # RESET SESSION
    # ============================================================

    def _on_reset_session(self) -> None:
        if self.df_raw_a.empty and self.df_raw_b.empty:
            toast(self, "Nothing to reset", tone="warning")
            return

        ok = confirm(
            self, "Reset Session?",
            "All loaded CDR data will be cleared from memory. "
            "The audit trail and user accounts are preserved. This cannot be undone.",
            danger=True, ok_text="Reset Session",
        )
        if not ok:
            return

        self.df_raw_a = pd.DataFrame()
        self.df_raw_b = pd.DataFrame()
        self.df_a = pd.DataFrame()
        self.df_b = pd.DataFrame()
        self._filter_state = {"phone": "", "use_date": False, "from": None, "to": None}

        self.tab_dashboard.clear()
        self.tab_network.clear()
        self.tab_map.clear()
        self.tab_anomalies.clear()
        self.tab_report.clear()
        self.tab_inspector.clear()
        self.tab_database.refresh()

        self.status_label.setText("Session reset — no data loaded.")
        self.toolbar.search.clear()
        self.audit.log(self.current_user, self.current_role, "RESET_SESSION", "Cleared all loaded CDR data.")
        toast(self, "Session reset", tone="success")

    # ============================================================
    # PROGRESS
    # ============================================================

    def _show_progress(self, label: str, maximum: int = 0) -> None:
        self.status_label.setText(label)
        self.progress_bar.setRange(0, maximum)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        QApplication.processEvents()

    def _update_progress(self, value: int, label: str | None = None) -> None:
        self.progress_bar.setValue(value)
        if label:
            self.status_label.setText(label)
        QApplication.processEvents()

    def _hide_progress(self) -> None:
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)

    # ============================================================
    # TOOLBAR WIRING
    # ============================================================

    def _wire_toolbar(self) -> None:
        self.toolbar.load_single.connect(self._on_load_single)
        self.toolbar.load_bulk.connect(self._on_load_bulk)
        self.toolbar.load_target_b.connect(self._on_load_target_b)
        self.toolbar.search_changed.connect(self._on_search_changed)
        self.toolbar.toggle_theme.connect(self._on_toggle_theme)
        self.toolbar.font_increase.connect(self._on_font_increase)
        self.toolbar.font_decrease.connect(self._on_font_decrease)
        self.toolbar.open_filters.connect(self._on_open_filters)
        self.toolbar.reset_session.connect(self._on_reset_session)

    # ============================================================
    # FILE LOADING
    # ============================================================

    def _on_load_single(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open CDR file", "", "CDR Files (*.csv *.xlsx *.xls);;All Files (*)"
        )
        if not path:
            return
        self._load_into_slot(path, target="A")

    def _on_load_bulk(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Open multiple CDR files", "", "CDR Files (*.csv *.xlsx *.xls);;All Files (*)"
        )
        if not paths:
            return
        self._load_bulk(paths)

    def _on_load_target_b(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Target B CDR", "", "CDR Files (*.csv *.xlsx *.xls);;All Files (*)"
        )
        if not path:
            return
        self._load_into_slot(path, target="B")

    def _load_into_slot(self, path, target) -> None:
        self._show_progress(f"Loading {Path(path).name}…", maximum=0)
        try:
            df = load_single_file(path)
        except Exception as e:
            self._hide_progress()
            log.exception("Load failed.")
            QMessageBox.critical(self, "Load failed", str(e))
            return
        self._hide_progress()

        if target == "A":
            self.df_raw_a = df
            self.df_a = df.copy()
        else:
            self.df_raw_b = df
            self.df_b = df.copy()

        if target == "A" and "timestamp" in df.columns and df["timestamp"].notna().any():
            self._filter_state["from"] = df["timestamp"].min().to_pydatetime()
            self._filter_state["to"] = df["timestamp"].max().to_pydatetime()

        label = f"Target {target}: {len(df):,} records"
        self.audit.log(self.current_user, self.current_role, f"LOAD_{target}", f"{label} from {path}")
        toast(self, label + " loaded", tone="success")
        self.status_label.setText(label)
        self._refresh_all()

    def _load_bulk(self, paths) -> None:
        total = len(paths)
        self._show_progress(f"Loading 0 of {total} files…", maximum=total)

        frames = []
        errors = []
        for i, p in enumerate(paths, start=1):
            self._update_progress(i, f"Loading {i} of {total}: {Path(p).name}")
            try:
                frames.append(load_single_file(p))
            except Exception as e:
                errors.append(f"{p}: {e}")

        if not frames:
            self._hide_progress()
            QMessageBox.critical(self, "Bulk load failed", "None of the files could be loaded.\n\n" + "\n".join(errors))
            return

        self._update_progress(total, "Combining files…")
        combined = pd.concat(frames, ignore_index=True)
        combined = combined.loc[:, ~combined.columns.duplicated()]
        combined.reset_index(drop=True, inplace=True)
        self._hide_progress()

        self.df_raw_a = combined
        self.df_a = combined.copy()

        if "timestamp" in combined.columns and combined["timestamp"].notna().any():
            self._filter_state["from"] = combined["timestamp"].min().to_pydatetime()
            self._filter_state["to"] = combined["timestamp"].max().to_pydatetime()

        label = f"Bulk: {total} files, {len(combined):,} records"
        self.audit.log(self.current_user, self.current_role, "LOAD_BULK", label)
        toast(self, label + " loaded", tone="success")
        self.status_label.setText(label)
        self._refresh_all()

    # ============================================================
    # MAP
    # ============================================================

    def _on_launch_map(self) -> None:
        if self.df_a.empty:
            QMessageBox.warning(self, "No data", "Load a CDR file first.")
            return

        self._show_progress("Generating map…", maximum=0)
        try:
            colocations = None
            if not self.df_b.empty:
                colocations = colocation_events(self.df_a, self.df_b)

            out = build_folium_map(
                self.df_a,
                self.df_b if not self.df_b.empty else None,
                colocations,
                show_heatmap=self.tab_map.heatmap_enabled(),
                show_triangulation=self.tab_map.triangulation_enabled(),
            )
            self._hide_progress()
            self.audit.log(self.current_user, self.current_role, "OPEN_MAP", f"Map opened: {out}")
            toast(self, "Map opened in browser", tone="success")
            self.status_label.setText("Map opened in browser.")
        except ValueError as e:
            self._hide_progress()
            QMessageBox.warning(self, "No coordinates", str(e))
        except Exception as e:
            self._hide_progress()
            log.exception("Map generation failed.")
            QMessageBox.critical(self, "Map error", str(e))

    # ============================================================
    # PDF EXPORT
    # ============================================================

    def _on_export_pdf(self) -> None:
        if self.df_a.empty:
            QMessageBox.warning(self, "No data", "Load a CDR file first.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF dossier", "dossier.pdf", "PDF Files (*.pdf)"
        )
        if not path:
            return

        self._show_progress("Generating PDF…", maximum=0)
        try:
            from reports.pdf_builder import build_dossier

            df = self.df_a
            risk = compute_risk(df)
            top = (
                df["party_b"].dropna().astype(str).value_counts().head(20)
                if "party_b" in df.columns else pd.Series(dtype=int)
            )
            towers = (
                df["cell_id"].dropna().astype(str).value_counts().head(20)
                if "cell_id" in df.columns else pd.Series(dtype=int)
            )

            build_dossier(
                path=Path(path),
                investigator=self.current_user,
                role=self.current_role,
                case_id="N/A",
                risk_score=risk.score,
                risk_level=risk.level,
                risk_rationale=risk.rationale,
                total_records=len(df),
                top_contacts=list(top.items()),
                towers=list(towers.items()),
            )
            self._hide_progress()
            self.audit.log(self.current_user, self.current_role, "EXPORT_PDF", str(path))
            toast(self, "PDF saved", tone="success")
            self.status_label.setText(f"PDF saved: {path}")
        except Exception as e:
            self._hide_progress()
            log.exception("PDF export failed.")
            QMessageBox.critical(self, "Export failed", str(e))

    # ============================================================
    # SEARCH
    # ============================================================

    def _on_search_changed(self, text: str) -> None:
        if hasattr(self, "tab_inspector"):
            self.tab_inspector.txt_search.setText(text)

    # ============================================================
    # REFRESH PIPELINE
    # ============================================================

    def _refresh_all(self) -> None:
        if self.df_a.empty:
            self.status_label.setText("No dataset loaded.")
            return

        df = self.df_a
        try:
            # 1. Graph Theory
            g = build_call_graph(df)
            centrality = centrality_table(g)
            communities = detect_communities(g)

            # 2. Prediction & Connections
            markov_preds = predict_next_call(df)
            mutual = mutual_contacts(df, self.df_b) if not self.df_b.empty else None

            # 3. Risk & Anomalies
            risk = compute_risk(df)
            anom_summary = summary(df)
            short = short_calls(df)
            night = night_calls(df)
            stat_anoms = statistical_anomalies(df)

            # Update Tabs
            self.tab_dashboard.update_data(df, risk, anom_summary, markov_preds)
            self.tab_network.update_data(g, centrality, mutual, communities)
            self.tab_map.update_data(df)
            self.tab_anomalies.update_data(short, night, anom_summary, stat_anoms)
            self.tab_report.update_data(df, risk)
            self.tab_inspector.update_data(df)
            self.tab_database.refresh()

            self.status_label.setText(
                f"{len(df):,} records · Risk: {risk.score}/100 ({risk.level})"
            )
        except Exception as e:
            log.exception("Refresh pipeline failed.")
            QMessageBox.critical(self, "Analysis error", str(e))

    # ============================================================
    # THEME + FONT
    # ============================================================

    def _apply_theme(self) -> None:
        palette = DARK if self._theme_is_dark else LIGHT
        self.setStyleSheet(stylesheet(palette, font_size=self._font_size))

    def _on_toggle_theme(self) -> None:
        self._theme_is_dark = not self._theme_is_dark
        self._apply_theme()

    def _on_font_increase(self) -> None:
        self._change_font(+1)

    def _on_font_decrease(self) -> None:
        self._change_font(-1)

    def _change_font(self, delta: int) -> None:
        new_size = self._font_size + delta
        new_size = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, new_size))
        if new_size == self._font_size:
            return
        self._font_size = new_size
        user_settings.set_value("font_size", new_size)
        self._apply_theme()

    # ============================================================
    # IDLE AUTO-LOCK
    # ============================================================

    def _install_idle_watch(self) -> None:
        self._idle_timer = QTimer(self)
        self._idle_timer.setInterval(1000)
        self._idle_timer.timeout.connect(self._tick_idle)
        self._idle_timer.start()
        QApplication.instance().installEventFilter(self)

    def _tick_idle(self) -> None:
        self._idle_seconds += 1
        remaining = max(0, IDLE_TIMEOUT_SECONDS - self._idle_seconds)
        if hasattr(self, "lock_label"):
            self.lock_label.setText(f"⏱  Auto-lock in {remaining}s")
        if self._idle_seconds >= IDLE_TIMEOUT_SECONDS:
            self._idle_seconds = 0
            self._auto_lock()

    def eventFilter(self, obj, event) -> bool:
        if event.type() in (QEvent.MouseMove, QEvent.MouseButtonPress, QEvent.KeyPress):
            self._idle_seconds = 0
        return super().eventFilter(obj, event)

    def _auto_lock(self) -> None:
        log.info("Auto-lock triggered.")
        try:
            self.audit.log(self.current_user, self.current_role, "AUTO_LOCK", "Idle timeout.")
        except Exception:
            log.exception("Audit on auto-lock failed.")
        try:
            self.db.close()
        except Exception:
            log.exception("DB close on auto-lock failed.")

        self.hide()
        from ui.dialogs.login_dialog import LoginDialog
        login = LoginDialog(self.db_path, parent=self)
        if login.exec_() != LoginDialog.Accepted or not login.username:
            QApplication.quit()
            return

        self.db.open()
        self.audit = AuditTrail(self.db)
        self.tab_database._audit = self.audit
        self.current_user = login.username
        self.current_role = login.role or "Junior Analyst"
        self.setWindowTitle(f"CDR Forensic System — {self.current_user} [{self.current_role}]")
        self.audit.log(self.current_user, self.current_role, "UNLOCK", "Session resumed after auto-lock.")
        self._idle_seconds = 0
        self.show()

    # ============================================================
    # KEYBOARD SHORTCUTS
    # ============================================================

    def _install_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+O"), self, activated=self._on_load_single)
        QShortcut(QKeySequence("Ctrl+Shift+O"), self, activated=self._on_load_bulk)
        QShortcut(QKeySequence("Ctrl+B"), self, activated=self._on_load_target_b)
        QShortcut(QKeySequence("Ctrl+L"), self, activated=self._auto_lock)
        QShortcut(QKeySequence("Ctrl+/"), self, activated=self._on_toggle_theme)
        QShortcut(QKeySequence("Ctrl+R"), self, activated=self._refresh_all)
        QShortcut(QKeySequence("Ctrl+="), self, activated=self._on_font_increase)
        QShortcut(QKeySequence("Ctrl+-"), self, activated=self._on_font_decrease)
        QShortcut(QKeySequence("Ctrl+P"), self, activated=self._on_print_current_tab)
        QShortcut(QKeySequence("Ctrl+F"), self, activated=self._on_open_filters)
        QShortcut(QKeySequence("Ctrl+Shift+R"), self, activated=self._on_reset_session)
        QShortcut(QKeySequence("Ctrl+Shift+P"), self, activated=self._print_under_cursor)

    # ============================================================
    # LIFECYCLE
    # ============================================================

    def closeEvent(self, event) -> None:
        if hasattr(self, "_idle_timer"):
            self._idle_timer.stop()
        try:
            self.audit.log(self.current_user, self.current_role, "LOGOUT", "Session ended.")
        except Exception:
            log.exception("Audit on close failed.")
        try:
            self.db.close()
        except Exception:
            log.exception("DB close failed.")
        super().closeEvent(event)