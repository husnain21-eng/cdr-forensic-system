"""Master QSS generator for the application.

Takes a Palette and returns a complete Qt stylesheet string.
Supports both light and dark themes without duplicating rules.
"""
from __future__ import annotations

from ui.theme.palette import Palette
from ui.theme.spacing import RADIUS, RADIUS_SM


def stylesheet(p: Palette) -> str:
    return f"""
    * {{
        font-family: 'Segoe UI', 'Inter', -apple-system, sans-serif;
        outline: none;
    }}
    QMainWindow, QDialog {{ background: {p.bg}; color: {p.text}; }}
    QWidget {{ color: {p.text}; font-size: 13px; }}

    /* ---------- Sidebar ---------- */
    QFrame#Sidebar {{
        background: {p.surface};
        border-right: 1px solid {p.border};
    }}
    QPushButton#NavItem {{
        text-align: left;
        padding: 10px 14px;
        border: none;
        border-radius: {RADIUS}px;
        color: {p.text_muted};
        font-weight: 500;
        background: transparent;
    }}
    QPushButton#NavItem:hover {{
        background: {p.surface_alt};
        color: {p.text};
    }}
    QPushButton#NavItem:checked {{
        background: {p.primary};
        color: {p.primary_text};
        font-weight: 600;
    }}

    /* ---------- Buttons ---------- */
    QPushButton {{
        background: {p.surface_alt};
        color: {p.text};
        border: 1px solid {p.border};
        border-radius: {RADIUS}px;
        padding: 8px 14px;
        font-weight: 500;
    }}
    QPushButton:hover {{ background: {p.border}; }}
    QPushButton:disabled {{ color: {p.text_muted}; background: {p.surface_alt}; }}

    QPushButton[role="primary"] {{
        background: {p.primary};
        color: {p.primary_text};
        border: none;
    }}
    QPushButton[role="primary"]:hover {{ background: {p.primary_hover}; }}

    QPushButton[role="danger"] {{
        background: {p.danger};
        color: white;
        border: none;
    }}

    /* ---------- Inputs ---------- */
    QLineEdit, QComboBox, QDateTimeEdit, QSpinBox, QDoubleSpinBox {{
        background: {p.surface};
        border: 1px solid {p.border};
        border-radius: {RADIUS_SM}px;
        padding: 8px 10px;
        selection-background-color: {p.primary};
    }}
    QLineEdit:focus, QComboBox:focus, QDateTimeEdit:focus {{
        border: 1px solid {p.primary};
    }}

    /* ---------- Tables ---------- */
    QTableView {{
        background: {p.surface};
        alternate-background-color: {p.surface_alt};
        gridline-color: {p.border};
        border: 1px solid {p.border};
        border-radius: {RADIUS}px;
        selection-background-color: {p.primary};
        selection-color: {p.primary_text};
    }}
    QHeaderView::section {{
        background: {p.surface_alt};
        color: {p.text_muted};
        padding: 8px;
        border: none;
        border-bottom: 1px solid {p.border};
        font-weight: 600;
        font-size: 12px;
    }}

    /* ---------- Group box ---------- */
    QGroupBox {{
        background: {p.surface};
        border: 1px solid {p.border};
        border-radius: {RADIUS}px;
        margin-top: 14px;
        padding: 14px;
        font-weight: 600;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
        color: {p.text_muted};
        font-size: 11px;
    }}

    /* ---------- Scrollbars ---------- */
    QScrollBar:vertical {{
        background: transparent; width: 10px; margin: 4px;
    }}
    QScrollBar::handle:vertical {{
        background: {p.border}; border-radius: 5px; min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {p.text_muted}; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}

    /* ---------- Status bar ---------- */
    QStatusBar {{
        background: {p.surface};
        color: {p.text_muted};
        border-top: 1px solid {p.border};
    }}
    """