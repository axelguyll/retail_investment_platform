"""
memo_pdf.py
Generates a PDF from the AI-written investment memo text using ReportLab.
Matches the platform's Navy Corporate visual style.
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# Color palette
DARK_BLUE = colors.HexColor("#1a3a5c")
MID_BLUE = colors.HexColor("#2d6a9f")
ACCENT = colors.HexColor("#c8a951")


def generate_memo_pdf(memo_text: str, property_name: str, market: str) -> bytes:
    """
    Convert markdown-formatted memo text to a styled PDF.
    Returns raw PDF bytes.

    Handles these markdown patterns:
      ## Heading       → section header style
      - bullet / * bullet → bullet paragraph
      **text**         → bold (stripped of asterisks)
      plain text       → body paragraph

    Args:
        memo_text: Markdown-formatted memo content
        property_name: Name of the property
        market: Market location

    Returns:
        bytes: PDF file content
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.9 * inch,
        rightMargin=0.9 * inch,
        topMargin=0.9 * inch,
        bottomMargin=0.9 * inch,
    )

    styles = getSampleStyleSheet()

    # ─── Custom Styles ────────────────────────────────────────────
    title_style = ParagraphStyle(
        "MemoTitle",
        fontName="Helvetica-Bold",
        fontSize=16,
        textColor=DARK_BLUE,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "MemoSubtitle",
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#94a3b8"),
        spaceAfter=2,
    )
    section_style = ParagraphStyle(
        "MemoSection",
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=DARK_BLUE,
        spaceBefore=14,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "MemoBody",
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#1e293b"),
        leading=14,
        spaceAfter=4,
    )
    bullet_style = ParagraphStyle(
        "MemoBullet",
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#1e293b"),
        leading=14,
        leftIndent=14,
        spaceAfter=2,
        bulletIndent=4,
    )

    story = []

    # ─── Header ───────────────────────────────────────────────────
    story.append(Paragraph(f"Investment Memo — {property_name}", title_style))
    story.append(Paragraph(
        f"{market} · Generated {datetime.now().strftime('%B %d, %Y')}",
        subtitle_style,
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=DARK_BLUE, spaceAfter=10))

    # ─── Parse memo text line by line ──────────────────────────────
    for line in memo_text.split("\n"):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 4))
            continue
        if line.startswith("## "):
            story.append(Paragraph(line[3:], section_style))
            story.append(HRFlowable(
                width="100%", thickness=0.5,
                color=colors.HexColor("#e2e8f0"), spaceAfter=4,
            ))
        elif line.startswith("- ") or line.startswith("* "):
            story.append(Paragraph(f"• {line[2:]}", bullet_style))
        else:
            # Strip inline markdown bold (**text**)
            clean = line.replace("**", "")
            story.append(Paragraph(clean, body_style))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
