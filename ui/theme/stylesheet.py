"""Master QSS generator for the application.

Supports both light and dark themes and user-controlled font size.
"""
from __future__ import annotations

from ui.theme.palette import Palette
from ui.theme.spacing import RADIUS, RADIUS_SM


def stylesheet(p: Palette, font_size: int = 14) -> str:
    fs = font_size
    header_fs = max(fs - 1, 10)
    small_fs = max(fs - 2, 10)

    return f"""
    * {{
        font-family: 'Segoe UI', 'Inter', -apple-system, sans-serif;
        outline: none;
    }}
    QMainWindow, QDialog {{ background: {p.bg}; color: {p.text}; }}
    QWidget {{ color: {p.text}; font-size: {fs}px; }}

    /* ---------- Tab bar ---------- */
    QTabWidget::pane {{
        border: none;
        background: {p.bg};
    }}
    QTabBar {{
        background: {p.surface};
        qproperty-drawBase: 0;
    }}
    QTabBar::tab {{
        background: {p.surface};
        color: {p.text_muted};
        padding: 10px 18px;
        margin-right: 2px;
        border: none;
        border-bottom: 2px solid transparent;
        font-size: {fs}px;
        font-weight: 500;
    }}
    QTabBar::tab:hover {{
        background: {p.surface_alt};
        color: {p.text};
    }}
    QTabBar::tab:selected {{
        color: {p.primary};
        border-bottom: 2px solid {p.primary};
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
        font-size: {fs}px;
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

    QToolButton {{
        background: transparent;
        color: {p.text};
        border: 1px solid transparent;
        border-radius: {RADIUS_SM}px;
        padding: 6px 10px;
        font-size: {fs}px;
    }}
    QToolButton:hover {{
        background: {p.surface_alt};
        border: 1px solid {p.border};
    }}

    /* ---------- Inputs ---------- */
    QLineEdit, QComboBox, QDateTimeEdit, QSpinBox, QDoubleSpinBox {{
        background: {p.surface};
        border: 1px solid {p.border};
        border-radius: {RADIUS_SM}px;
        padding: 8px 10px;
        selection-background-color: {p.primary};
        font-size: {fs}px;
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
        font-size: {fs}px;
    }}
    QHeaderView::section {{
        background: {p.surface_alt};
        color: {p.text_muted};
        padding: 8px;
        border: none;
        border-bottom: 1px solid {p.border};
        font-weight: 600;
        font-size: {header_fs}px;
    }}

    /* ---------- Group box ---------- */
    QGroupBox {{
        background: {p.surface};
        border: 1px solid {p.border};
        border-radius: {RADIUS}px;
        margin-top: 14px;
        padding: 14px;
        font-weight: 600;
        font-size: {fs}px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
        color: {p.text_muted};
        font-size: {small_fs}px;
    }}

    QCheckBox {{
        font-size: {fs}px;
    }}

    QLabel {{
        font-size: {fs}px;
    }}

    /* ---------- Scrollbars ---------- */
    QScrollBar:vertical {{
        background: transparent; width: 12px; margin: 4px;
    }}
    QScrollBar::handle:vertical {{
        background: {p.border}; border-radius: 6px; min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {p.text_muted}; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}

    /* ---------- Status bar ---------- */
    QStatusBar {{
        background: {p.surface};
        color: {p.text_muted};
        border-top: 1px solid {p.border};
        font-size: {small_fs}px;
    }}
    """