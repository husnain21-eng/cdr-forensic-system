"""Print helper — renders widgets or full tables to a printer."""
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPageLayout, QPainter, QTextDocument
from PyQt5.QtPrintSupport import QPrinter, QPrintPreviewDialog
from PyQt5.QtWidgets import QDialog, QScrollArea, QWidget, QTableView


def print_widget(widget: QWidget, parent: QWidget | None = None, landscape: bool = True) -> bool:
    """Show a live print preview. If it's a table, print ALL data."""
    printer = QPrinter(QPrinter.HighResolution)
    printer.setPageOrientation(QPageLayout.Landscape if landscape else QPageLayout.Portrait)
    printer.setDocName("CDR Forensic Report")

    preview = QPrintPreviewDialog(printer, parent)
    preview.setWindowTitle("Print Preview")
    preview.resize(1000, 720)

    # Check if we are printing a DataTable (QTableView)
    if isinstance(widget, QTableView) or widget.metaObject().className() == "DataTable":
        # Print the full table data via HTML
        preview.paintRequested.connect(lambda prt: _print_full_table(widget, prt))
    else:
        # Print the visual widget (charts, cards)
        preview.paintRequested.connect(lambda prt: _render_to_printer(widget, prt))

    return preview.exec_() == QDialog.Accepted


def _print_full_table(table_view: QTableView, printer: QPrinter) -> None:
    """Convert the entire DataFrame to HTML and print across multiple pages."""
    model = table_view.model()
    if not model: return

    rows = model.rowCount()
    cols = model.columnCount()

    html = "<html><head><style>"
    html += "table { width: 100%; border-collapse: collapse; font-family: Arial, sans-serif; font-size: 10pt; }"
    html += "th { background-color: #2563EB; color: white; padding: 8px; text-align: left; }"
    html += "td { border-bottom: 1px solid #E5E7EB; padding: 6px; }"
    html += "tr:nth-child(even) { background-color: #F9FAFB; }"
    html += "</style></head><body>"

    # Header
    html += "<h2>Data Export</h2><table><thead><tr>"
    for c in range(cols):
        header = model.headerData(c, Qt.Horizontal)
        html += f"<th>{header}</th>"
    html += "</tr></thead><tbody>"

    # Body (All Rows)
    for r in range(rows):
        html += "<tr>"
        for c in range(cols):
            val = model.data(model.index(r, c))
            html += f"<td>{val or ''}</td>"
        html += "</tr>"
    html += "</tbody></table></body></html>"

    doc = QTextDocument()
    doc.setHtml(html)
    doc.print_(printer)


def _render_to_printer(widget: QWidget, printer: QPrinter) -> None:
    """Render a visual widget (chart/card) to printer."""
    if isinstance(widget, QScrollArea):
        inner = widget.widget()
        if inner is not None:
            widget = inner

    pixmap = widget.grab()
    if pixmap.isNull():
        return

    painter = QPainter(printer)
    try:
        viewport = painter.viewport()
        size = pixmap.size()
        size.scale(viewport.size(), Qt.KeepAspectRatio)
        painter.setViewport(viewport.x(), viewport.y(), size.width(), size.height())
        painter.setWindow(pixmap.rect())
        painter.drawPixmap(0, 0, pixmap)
    finally:
        painter.end()