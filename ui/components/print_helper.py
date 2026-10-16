"""Print helper — shows a live preview dialog before printing.

The preview dialog has its own Print button. Users can inspect the
rendered tab before sending it to a printer, and can zoom to check
readability.
"""
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPageLayout, QPainter
from PyQt5.QtPrintSupport import QPrinter, QPrintPreviewDialog
from PyQt5.QtWidgets import QDialog, QScrollArea, QWidget


def print_widget(
    widget: QWidget,
    parent: QWidget | None = None,
    landscape: bool = True,
) -> bool:
    """Show a live print preview. Returns True if the user printed.

    The dialog contains a Print button — clicking it sends the
    currently-rendered tab to the selected printer.
    """
    printer = QPrinter(QPrinter.HighResolution)
    printer.setPageOrientation(
        QPageLayout.Landscape if landscape else QPageLayout.Portrait
    )
    printer.setDocName("CDR Forensic Report")

    preview = QPrintPreviewDialog(printer, parent)
    preview.setWindowTitle("Print Preview")
    preview.resize(1000, 720)

    # Called every time the preview redraws a page
    def render(prt: QPrinter) -> None:
        _render_to_printer(widget, prt)

    preview.paintRequested.connect(render)

    # exec_() returns Accepted when the user clicks Print inside the dialog
    result = preview.exec_()
    return result == QDialog.Accepted


def _render_to_printer(widget: QWidget, printer: QPrinter) -> None:
    """Render a widget to the given printer, preserving aspect ratio."""
    # If the widget is a QScrollArea, unwrap to the inner content
    if isinstance(widget, QScrollArea):
        inner = widget.widget()
        if inner is not None:
            widget = inner

    # Grab the widget's full render as a pixmap
    pixmap = widget.grab()
    if pixmap.isNull():
        return

    painter = QPainter(printer)
    try:
        viewport = painter.viewport()
        size = pixmap.size()
        size.scale(viewport.size(), Qt.KeepAspectRatio)
        painter.setViewport(
            viewport.x(), viewport.y(),
            size.width(), size.height(),
        )
        painter.setWindow(pixmap.rect())
        painter.drawPixmap(0, 0, pixmap)
    finally:
        painter.end()