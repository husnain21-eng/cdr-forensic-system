"""A4 PDF dossier generation with watermarks and headers/footers.

Uses ReportLab's onFirstPage/onLaterPages hooks (the correct way) so
the watermark actually renders on every page.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


MARGIN = 36  # 0.5 inch
WATERMARK_ALPHA = 0.08


def build_dossier(
    path: Path,
    investigator: str,
    role: str,
    case_id: str,
    risk_score: int,
    risk_level: str,
    risk_rationale: str,
    total_records: int,
    top_contacts: list[tuple[str, int]],
    towers: list[tuple[str, int]],
) -> None:
    """Generate an official PDF dossier at `path`."""
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title="CDR Investigative Dossier",
        author=investigator,
    )

    styles = getSampleStyleSheet()
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    story = [
        Paragraph("OFFICIAL INVESTIGATION DOSSIER", styles["Heading1"]),
        Spacer(1, 6),
        Paragraph(
            f"<b>Case ID:</b> {case_id or 'N/A'} &nbsp;&nbsp; "
            f"<b>Generated:</b> {generated}",
            styles["Normal"],
        ),
        Spacer(1, 14),

        Paragraph("1. Investigator", styles["Heading2"]),
        Paragraph(f"{investigator} &mdash; role: {role}", styles["Normal"]),
        Spacer(1, 12),

        Paragraph("2. Risk Assessment (Documented Heuristic)", styles["Heading2"]),
        Paragraph(
            f"<b>Score:</b> {risk_score}/100 &nbsp; "
            f"<b>Level:</b> {risk_level}",
            styles["Normal"],
        ),
        Paragraph(risk_rationale, styles["Normal"]),
        Spacer(1, 12),

        Paragraph("3. Dataset Summary", styles["Heading2"]),
        Paragraph(f"Total records analyzed: {total_records:,}", styles["Normal"]),
        Spacer(1, 12),

        Paragraph("4. Top Interlocutors", styles["Heading2"]),
        _build_table([["Phone Number", "Interactions"]] + list(top_contacts)),
        Spacer(1, 12),

        Paragraph("5. Cell Towers / Sites", styles["Heading2"]),
        _build_table([["Site ID", "Records"]] + list(towers)),
        Spacer(1, 12),

        Paragraph(
            "<i>This dossier was produced by the CDR Forensic System. "
            "Chain of custody is recorded in the tamper-evident audit log.</i>",
            styles["Italic"],
        ),
    ]

    on_page = _on_page(investigator)
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)


def _build_table(rows: list[list]) -> Table:
    """Build a consistently styled table, or a placeholder if empty."""
    if len(rows) <= 1:
        return Paragraph("No data available.", getSampleStyleSheet()["Normal"])

    table = Table(rows, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def _on_page(investigator: str):
    """Return a page callback used by ReportLab for every page."""

    def callback(canvas, doc):
        canvas.saveState()

        # Header
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(colors.HexColor("#C0392B"))
        canvas.drawString(
            MARGIN,
            A4[1] - 20,
            "RESTRICTED / LAW ENFORCEMENT USE ONLY — STRICTLY CONFIDENTIAL",
        )
        canvas.setStrokeColor(colors.HexColor("#CBD5E1"))
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, A4[1] - 24, A4[0] - MARGIN, A4[1] - 24)

        # Diagonal watermark
        canvas.saveState()
        canvas.setFont("Helvetica-Bold", 46)
        canvas.setFillColor(
            colors.HexColor("#B0B0B0"), alpha=WATERMARK_ALPHA
        )
        canvas.translate(A4[0] / 2, A4[1] / 2)
        canvas.rotate(45)
        canvas.drawCentredString(0, 0, f"CONFIDENTIAL — {investigator}")
        canvas.restoreState()

        # Footer
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#555555"))
        canvas.drawString(
            MARGIN,
            20,
            f"Investigator: {investigator} | Case Dossier",
        )
        canvas.drawRightString(
            A4[0] - MARGIN,
            20,
            f"Page {doc.page} | HMAC-signed audit chain active",
        )

        canvas.restoreState()

    return callback