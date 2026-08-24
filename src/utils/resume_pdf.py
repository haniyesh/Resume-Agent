from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)


def merge_revised_resume(resume_data, review_data):
    """Return the original resume with available revised sections applied."""
    merged = {}
    for section_name, original_content in (resume_data or {}).items():
        review = (review_data or {}).get(section_name) or {}
        revised_content = review.get("revised_content")
        merged[section_name] = (
            revised_content if revised_content not in (None, "", [], {}) else original_content
        )
    return merged


def _text(value):
    if value is None:
        return ""
    return escape(str(value))


def _content_flowables(value, styles, level=0):
    if value in (None, "", [], {}):
        return []

    if isinstance(value, dict):
        flowables = []
        for key, item in value.items():
            label = Paragraph(f"<b>{_text(key).replace('_', ' ').title()}</b>", styles["Field"])
            flowables.append(label)
            flowables.extend(_content_flowables(item, styles, level + 1))
        return flowables

    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            item_flowables = _content_flowables(item, styles, level + 1)
            if item_flowables:
                items.append(ListItem(item_flowables, leftIndent=12))
        return [ListFlowable(items, bulletType="bullet", leftIndent=18)] if items else []

    return [Paragraph(_text(value).replace("\n", "<br/>"), styles["Body"])]


def generate_resume_pdf(resume_data):
    """Generate a revised resume using the supplied resume PDF design."""
    overlay_buffer = BytesIO()
    document = SimpleDocTemplate(
        overlay_buffer,
        pagesize=A4,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=1.65 * inch,
        bottomMargin=0.6 * inch,
        title="Revised Resume",
    )

    base_styles = getSampleStyleSheet()
    styles = {
        "Name": ParagraphStyle(
            "Name",
            parent=base_styles["Title"],
            alignment=TA_CENTER,
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#17324D"),
            spaceAfter=12,
        ),
        "Section": ParagraphStyle(
            "Section",
            parent=base_styles["Heading2"],
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#176B87"),
            spaceBefore=10,
            spaceAfter=5,
        ),
        "Field": ParagraphStyle(
            "Field",
            parent=base_styles["BodyText"],
            fontSize=9.5,
            leading=12,
            spaceBefore=3,
            spaceAfter=2,
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=base_styles["BodyText"],
            fontSize=9.5,
            leading=13,
            spaceAfter=5,
        ),
    }

    story = []
    for index, (section_name, content) in enumerate((resume_data or {}).items()):
        if index == 0 and isinstance(content, dict) and content.get("full_name"):
            story.append(Paragraph(_text(content["full_name"]), styles["Name"]))
            contact_fields = [
                content.get("email"),
                content.get("phone"),
                content.get("linkedin"),
                content.get("github"),
                content.get("website"),
            ]
            contact = " | ".join(_text(item) for item in contact_fields if item)
            if contact:
                story.append(Paragraph(contact, styles["Body"]))
        else:
            story.append(Paragraph(_text(section_name).replace("_", " ").title(), styles["Section"]))
            story.extend(_content_flowables(content, styles))
        if index < len(resume_data) - 1:
            story.append(Spacer(1, 4))

    document.build(
        story or [Paragraph("Revised Resume", styles["Name"])],
        onFirstPage=lambda canvas, doc: _draw_template_mask(
            canvas, doc, resume_data, first_page=True
        ),
        onLaterPages=lambda canvas, doc: _draw_template_mask(
            canvas, doc, resume_data, first_page=False
        ),
    )

    template_path = Path(__file__).resolve().parents[1] / "data" / "resume.pdf"
    template_reader = PdfReader(str(template_path))
    overlay_reader = PdfReader(overlay_buffer)
    writer = PdfWriter()

    for index, overlay_page in enumerate(overlay_reader.pages):
        template_page = template_reader.pages[min(index, len(template_reader.pages) - 1)]
        template_page.merge_page(overlay_page)
        writer.add_page(template_page)

    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def _draw_template_mask(canvas, document, resume_data, first_page):
    """Hide the template's sample text while retaining its page design."""
    page_width, page_height = A4
    canvas.saveState()
    canvas.setFillColor(colors.white)
    canvas.rect(0.35 * inch, 0.35 * inch, page_width - 0.7 * inch, page_height - 0.7 * inch, fill=1, stroke=0)

    if first_page:
        personal_info = next(iter((resume_data or {}).values()), {})
        if not isinstance(personal_info, dict):
            personal_info = {}

        canvas.setFillColor(colors.HexColor("#F7F7F7"))
        canvas.rect(0, page_height - 1.55 * inch, page_width, 1.55 * inch, fill=1, stroke=0)
        canvas.setStrokeColor(colors.HexColor("#0B9A9A"))
        canvas.setLineWidth(0.7)
        canvas.line(0.65 * inch, page_height - 0.78 * inch, page_width - 0.65 * inch, page_height - 0.78 * inch)

        canvas.setFillColor(colors.HexColor("#078C95"))
        canvas.setFont("Helvetica-Bold", 20)
        canvas.drawString(0.65 * inch, page_height - 0.48 * inch, str(personal_info.get("full_name", "Revised Resume")))

        canvas.setFillColor(colors.HexColor("#222222"))
        canvas.setFont("Helvetica", 14)
        canvas.drawRightString(
            page_width - 0.65 * inch,
            page_height - 0.48 * inch,
            str(personal_info.get("headline", "Resume")),
        )

        contact_fields = [
            personal_info.get("phone"),
            personal_info.get("email"),
            personal_info.get("address"),
            personal_info.get("linkedin"),
            personal_info.get("github"),
            personal_info.get("website"),
        ]
        contact = "   |   ".join(str(item) for item in contact_fields if item and not isinstance(item, dict))
        canvas.setFont("Helvetica", 9.5)
        canvas.drawString(0.65 * inch, page_height - 1.08 * inch, contact)

    canvas.restoreState()
