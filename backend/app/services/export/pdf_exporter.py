import io
from datetime import datetime

from fpdf import FPDF


class _PlaybookPDF(FPDF):
    def __init__(self, org_name: str, version: int):
        super().__init__()
        self._org_name = org_name
        self._version = version

    def header(self):
        pass  # Title page handles its own header

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 100, 100)
        self.cell(
            0,
            10,
            f"{self._org_name} — Contract Standards Playbook v{self._version}    |    Page {self.page_no()}",
            align="C",
        )


def export_playbook_to_pdf(playbook, org_name: str = "Your Organization") -> bytes:
    """
    Render an OrgPlaybook as a PDF file.
    playbook: OrgPlaybook SQLAlchemy model.
    Returns raw bytes of the PDF.
    """
    pdf = _PlaybookPDF(org_name=org_name, version=playbook.version)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # ── Title page ─────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 26)
    pdf.set_text_color(15, 23, 41)  # dark navy
    pdf.ln(30)
    pdf.multi_cell(0, 14, f"{org_name}", align="C")

    pdf.set_font("Helvetica", "", 18)
    pdf.multi_cell(0, 10, "Contract Standards Playbook", align="C")
    pdf.ln(8)

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(
        0,
        7,
        f"Version {playbook.version}  ·  "
        f"Generated {_fmt_date(playbook.generated_at)}  ·  "
        f"{playbook.doc_count} source documents",
        align="C",
    )
    pdf.ln(8)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(192, 0, 0)
    pdf.multi_cell(0, 7, "CONFIDENTIAL — INTERNAL USE ONLY", align="C")

    # ── Sections ────────────────────────────────────────────────────────────
    sections = playbook.sections or []
    for section in sections:
        pdf.add_page()
        _write_section_pdf(pdf, section)

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


def _write_section_pdf(pdf: _PlaybookPDF, section: dict) -> None:
    title = section.get("title", section.get("clause_type", "Section"))

    # Section heading
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(15, 23, 41)
    pdf.multi_cell(0, 10, title)
    pdf.ln(4)

    # Non-Negotiables
    non_neg = section.get("non_negotiables", [])
    if non_neg:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(192, 0, 0)
        pdf.cell(0, 8, "Non-Negotiables", ln=True)
        pdf.set_font("Helvetica", "", 10)
        for item in non_neg:
            pdf.set_text_color(192, 0, 0)
            pdf.multi_cell(0, 6, f"  •  {item}")
        pdf.ln(3)

    # Standard Positions
    positions = section.get("standard_positions", [])
    if positions:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(15, 23, 41)
        pdf.cell(0, 8, "Standard Positions", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(40, 40, 40)
        for pos in positions:
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(0, 6, pos.get("description", ""))
            pdf.set_font("Helvetica", "", 10)
            if pos.get("acceptable_range"):
                pdf.multi_cell(0, 6, f"  Range: {pos['acceptable_range']}")
            if pos.get("rationale"):
                pdf.multi_cell(0, 6, f"  Rationale: {pos['rationale']}")
            pdf.ln(2)
        pdf.ln(2)

    # Red Flags
    flags = section.get("red_flags", [])
    if flags:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(230, 108, 0)
        pdf.cell(0, 8, "Red Flags", ln=True)
        pdf.set_font("Helvetica", "", 10)
        for flag in flags:
            pdf.set_text_color(230, 108, 0)
            pdf.multi_cell(0, 6, f"  ⚠  {flag}")
        pdf.ln(3)

    # Industry Baseline
    baseline = section.get("industry_baseline", "")
    if baseline:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(15, 23, 41)
        pdf.cell(0, 8, "Industry Baseline", ln=True)
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(80, 80, 80)
        pdf.multi_cell(0, 6, baseline)


def _fmt_date(dt) -> str:
    if isinstance(dt, datetime):
        return dt.strftime("%B %d, %Y")
    if isinstance(dt, str):
        try:
            return datetime.fromisoformat(dt).strftime("%B %d, %Y")
        except ValueError:
            return dt
    return str(dt)
