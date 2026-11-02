"""Modern Top Toolbar with strict spacing."""
from __future__ import annotations

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QToolButton, QGraphicsDropShadowEffect
)
from PyQt5.QtGui import QColor


class TopToolbar(QFrame):
    load_single = pyqtSignal()
    load_bulk = pyqtSignal()
    load_target_b = pyqtSignal()
    reset_session = pyqtSignal()
    toggle_theme = pyqtSignal()
    open_filters = pyqtSignal()
    search_changed = pyqtSignal(str)
    font_decrease = pyqtSignal()
    font_increase = pyqtSignal()
    call_type_changed = pyqtSignal(str)

    def __init__(self, username: str, role: str, parent=None):
        super().__init__(parent)
        self.setObjectName("TopToolbar")
        self.setFixedHeight(64)

        self.setStyleSheet("""
            QFrame#TopToolbar {
                background-color: #1E293B;
                border-bottom: 1px solid #334155;
            }
            QLineEdit {
                background-color: #0F172A;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 16px;
                padding: 6px 16px;
                font-size: 13px;
            }
            QLineEdit:focus { border: 1px solid #3B82F6; }
            QComboBox {
                background-color: #0F172A;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 13px;
            }
            QToolButton {
                color: #CBD5E1;
                background: transparent;
                border: none;
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
            }
            QToolButton:hover { background-color: #334155; color: #F8FAFC; }
            QPushButton {
                background-color: #2563EB;
                color: white;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #1D4ED8; }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)  # Reduced spacing to fit more

        # --- ZONE 1: SEARCH & FILTER ---
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 Search...")
        self.search.setClearButtonEnabled(True)
        self.search.setMinimumWidth(180)
        self.search.setMaximumWidth(250)  # Prevents it from growing too large
        self.search.textChanged.connect(self.search_changed.emit)

        self.cmb_call_type = QComboBox()
        self.cmb_call_type.addItems(["All Events", "Outgoing", "Incoming", "SMS", "Missed"])
        self.cmb_call_type.setMinimumWidth(110)
        self.cmb_call_type.currentTextChanged.connect(self.call_type_changed.emit)

        layout.addWidget(self.search)
        layout.addWidget(self.cmb_call_type)

        # Invisible Spacer to push actions to the right
        layout.addStretch(1)

        # --- ZONE 2: ACTIONS ---
        btn_single = QPushButton("📁 Open CDR")
        btn_single.clicked.connect(self.load_single.emit)
        layout.addWidget(btn_single)

        btn_bulk = QToolButton()
        btn_bulk.setText("📚 Bulk")
        btn_bulk.clicked.connect(self.load_bulk.emit)
        layout.addWidget(btn_bulk)

        btn_target_b = QToolButton()
        btn_target_b.setText("🎯 Target B")
        btn_target_b.clicked.connect(self.load_target_b.emit)
        layout.addWidget(btn_target_b)

        btn_filters = QToolButton()
        btn_filters.setText("⚙️ Filters")
        btn_filters.clicked.connect(self.open_filters.emit)
        layout.addWidget(btn_filters)

        btn_reset = QToolButton()
        btn_reset.setText("🔄")
        btn_reset.setToolTip("Reset Session")
        btn_reset.clicked.connect(self.reset_session.emit)
        layout.addWidget(btn_reset)

        # --- ZONE 3: SETTINGS ---
        # Add a visual separator line
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setStyleSheet("color: #334155;")
        layout.addWidget(line)

        btn_font_minus = QToolButton()
        btn_font_minus.setText("A−")
        btn_font_minus.clicked.connect(self.font_decrease.emit)
        layout.addWidget(btn_font_minus)

        btn_font_plus = QToolButton()
        btn_font_plus.setText("A+")
        btn_font_plus.clicked.connect(self.font_increase.emit)
        layout.addWidget(btn_font_plus)

        btn_theme = QToolButton()
        btn_theme.setText("🌙")
        btn_theme.clicked.connect(self.toggle_theme.emit)
        layout.addWidget(btn_theme)

        # --- ZONE 4: USER BADGE ---
        user_label = QLabel(f"👤 <b>{username.split()[0]}</b>")  # Only show first name to save space
        user_label.setToolTip(f"Logged in as: {username} ({role})")
        user_label.setStyleSheet("color: #F8FAFC; padding-left: 8px;")
        layout.addWidget(user_label)