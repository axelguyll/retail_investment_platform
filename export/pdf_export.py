"""
pdf_export.py
Generates a clean 1-2 page pro forma PDF using ReportLab.

Sections:
  1. Deal Summary
  2. Sources & Uses
  3. 10-Year Cash Flow Projection Table
  4. Return Metrics
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

# Color palette
DARK_BLUE = colors.HexColor("#1a3a5c")
MID_BLUE = colors.HexColor("#2d6a9f")
LIGHT_BLUE = colors.HexColor("#e8f0f8")
ACCENT = colors.HexColor("#c8a951")
WHITE = colors.white
LIGHT_GRAY = colors.HexColor("#f5f5f5")
MED_GRAY = colors.HexColor("#cccccc")
TEXT_DARK = colors.HexColor("#1a1a2e")


def fmt_currency(val: float) -> str:
    if val >= 1_000_000:
        return f"${val / 1_000_000:.2f}M"
    elif val >= 1_000:
        return f"${val:,.0f}"
    return f"${val:.2f}"


def fmt_pct(val: float) -> str:
    return f"{val * 100:.2f}%"


def fmt_num(val: float) -> str:
    return f"{val:,.0f}"


def generate_pdf(inputs, results) -> bytes:
    """
    Generate a PDF pro forma and return it as bytes.

    Args:
        inputs: DealInputs dataclass
        results: UnderwritingResults dataclass

    Returns:
        bytes: PDF file content
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
    )

    styles = getSampleStyleSheet()
    story = []

    # ─── Custom Styles ──────────────────────────────────────────
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontSize=18,
        textColor=WHITE,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=ACCENT,
        alignment=TA_CENTER,
        fontName="Helvetica",
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Normal"],
        fontSize=10,
        textColor=WHITE,
        fontName="Helvetica-Bold",
        spaceAfter=2,
        spaceBefore=2,
        leftIndent=6,
    )
    label_style = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=8.5,
        textColor=TEXT_DARK,
        fontName="Helvetica-Bold",
    )
    value_style = ParagraphStyle(
        "Value",
        parent=styles["Normal"],
        fontSize=8.5,
        textColor=TEXT_DARK,
        fontName="Helvetica",
        alignment=TA_RIGHT,
    )
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=7,
        textColor=colors.gray,
        alignment=TA_CENTER,
    )

    page_width = letter[0] - 1.2 * inch  # usable width

    # ─── Header Banner ───────────────────────────────────────────
    header_data = [
        [Paragraph("RETAIL REAL ESTATE PRO FORMA", title_style)],
        [Paragraph(f"{inputs.property_name}  ·  {inputs.market}", subtitle_style)],
        [Paragraph(f"Prepared {datetime.now().strftime('%B %d, %Y')}", subtitle_style)],
    ]
    header_table = Table(header_data, colWidths=[page_width])
    header_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), DARK_BLUE),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    story.append(header_table)
    story.append(Spacer(1, 0.15 * inch))

    # ─── Helper: Section Header ───────────────────────────────────
    def section_header(title: str):
        t = Table([[Paragraph(title.upper(), section_style)]], colWidths=[page_width])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), MID_BLUE),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        return t

    # ─── Helper: Two-column key-value table ──────────────────────
    def kv_table(rows: list[tuple[str, str]], cols: int = 2):
        """Build a clean key-value grid. cols=2 means 2 pairs per row (4 columns total)."""
        col_w = page_width / (cols * 2)
        tdata = []
        for i in range(0, len(rows), cols):
            row_cells = []
            for j in range(cols):
                if i + j < len(rows):
                    k, v = rows[i + j]
                    row_cells.append(Paragraph(k, label_style))
                    row_cells.append(Paragraph(v, value_style))
                else:
                    row_cells.append(Paragraph("", label_style))
                    row_cells.append(Paragraph("", value_style))
            tdata.append(row_cells)
        t = Table(tdata, colWidths=[col_w] * (cols * 2))
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), WHITE),
                    ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, LIGHT_GRAY]),
                    ("GRID", (0, 0), (-1, -1), 0.25, MED_GRAY),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        return t

    # ─── 1. Deal Summary ─────────────────────────────────────────
    story.append(section_header("1. Deal Summary"))
    story.append(Spacer(1, 0.05 * inch))

    summary_rows = [
        ("Property Name", inputs.property_name),
        ("Market", inputs.market),
        ("Square Footage", f"{inputs.square_footage:,.0f} SF"),
        ("Purchase Price", fmt_currency(inputs.purchase_price)),
        ("Price per SF", fmt_currency(results.price_per_sf)),
        ("In-Place NOI (Yr 1)", fmt_currency(results.noi_year1)),
        ("NOI per SF", fmt_currency(results.noi_per_sf)),
        ("Going-In Cap Rate", fmt_pct(inputs.cap_rate)),
        ("Vacancy Rate", fmt_pct(inputs.vacancy_rate)),
        ("Exit Cap Rate", fmt_pct(inputs.exit_cap_rate)),
        ("Hold Period", f"{inputs.hold_period} Years"),
        ("NOI Growth Rate", fmt_pct(inputs.noi_growth_rate)),
    ]
    story.append(kv_table(summary_rows, cols=2))
    story.append(Spacer(1, 0.12 * inch))

    # ─── 2. Sources & Uses ───────────────────────────────────────
    story.append(section_header("2. Sources & Uses"))
    story.append(Spacer(1, 0.05 * inch))

    su_rows = [
        ("Purchase Price", fmt_currency(inputs.purchase_price)),
        ("Loan Amount", fmt_currency(results.loan_amount)),
        ("Loan-to-Value", fmt_pct(results.loan_to_value)),
        ("Equity Invested", fmt_currency(results.equity_invested)),
        ("Interest Rate", fmt_pct(inputs.interest_rate)),
        ("Amortization", f"{inputs.amortization_years} Years"),
        ("Monthly Payment", fmt_currency(results.monthly_payment)),
        ("Annual Debt Service", fmt_currency(results.annual_debt_service)),
    ]
    story.append(kv_table(su_rows, cols=2))
    story.append(Spacer(1, 0.12 * inch))

    # ─── 3. Return Metrics ───────────────────────────────────────
    story.append(section_header("3. Return Metrics"))
    story.append(Spacer(1, 0.05 * inch))

    irr_display = fmt_pct(results.irr) if results.irr is not None else "N/A"
    metrics_rows = [
        ("Levered IRR", irr_display),
        ("Equity Multiple", f"{results.equity_multiple:.2f}x"),
        ("Cash-on-Cash (Yr 1)", fmt_pct(results.cash_on_cash_year1)),
        ("DSCR (Yr 1)", f"{results.dscr_year1:.2f}x"),
        ("Year 1 Cash Flow", fmt_currency(results.cash_flow_year1)),
        ("Net Sale Proceeds", fmt_currency(results.net_sale_proceeds)),
    ]
    story.append(kv_table(metrics_rows, cols=2))
    story.append(Spacer(1, 0.15 * inch))

    # ─── 4. Cash Flow Projection ─────────────────────────────────
    story.append(section_header("4. Cash Flow Projection"))
    story.append(Spacer(1, 0.05 * inch))

    cf = results.cash_flow_table
    cf_header = [
        "Year", "NOI", "Debt Service", "CF (Ops)", "Sale Proceeds", "Total CF", "Loan Balance"
    ]
    cf_data = [cf_header]
    for _, row in cf.iterrows():
        cf_data.append(
            [
                str(int(row["Year"])),
                fmt_currency(row["NOI"]),
                fmt_currency(row["Debt Service"]),
                fmt_currency(row["Cash Flow (Ops)"]),
                fmt_currency(row["Net Sale Proceeds"]) if row["Net Sale Proceeds"] > 0 else "—",
                fmt_currency(row["Total Cash Flow"]),
                fmt_currency(row["Loan Balance"]),
            ]
        )

    col_widths = [
        0.42 * inch,  # Year
        0.85 * inch,  # NOI
        0.90 * inch,  # Debt Service
        0.85 * inch,  # CF Ops
        0.95 * inch,  # Sale Proceeds
        0.85 * inch,  # Total CF
        0.90 * inch,  # Loan Balance
    ]

    cf_table_obj = Table(cf_data, colWidths=col_widths, repeatRows=1)
    cf_table_obj.setStyle(
        TableStyle(
            [
                # Header row
                ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 7.5),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                # Data rows
                ("FONTSIZE", (0, 1), (-1, -1), 7.5),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("ALIGN", (0, 1), (0, -1), "CENTER"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
                # Exit year highlight
                ("BACKGROUND", (0, len(cf_data) - 1), (-1, len(cf_data) - 1), LIGHT_BLUE),
                ("FONTNAME", (0, len(cf_data) - 1), (-1, len(cf_data) - 1), "Helvetica-Bold"),
                # Grid
                ("GRID", (0, 0), (-1, -1), 0.25, MED_GRAY),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(cf_table_obj)
    story.append(Spacer(1, 0.2 * inch))

    # ─── Footer ──────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=MED_GRAY))
    story.append(Spacer(1, 0.05 * inch))
    story.append(
        Paragraph(
            "This pro forma is for illustrative purposes only. All projections are estimates and not guarantees of future performance. "
            f"Generated by Retail Investment Platform · {datetime.now().strftime('%B %d, %Y')}",
            footer_style,
        )
    )

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
