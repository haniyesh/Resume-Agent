from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def merge_revised_resume(resume_data, review_data):
    """Return the original resume with available revised sections applied."""
    merged = {}
    for section_name, original_content in (resume_data or {}).items():
        if section_name == "education":
            merged[section_name] = original_content
            continue

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


def _metadata(item):
    location = item.get("location", {})
    location_text = ""
    if isinstance(location, dict):
        location_text = ", ".join(
            str(location.get(field))
            for field in ("city", "state")
            if location.get(field)
        )

    dates = " - ".join(
        str(item.get(field))
        for field in ("start_date", "end_date")
        if item.get(field)
    )
    return " | ".join(value for value in (location_text, dates) if value)


def _entry_flowables(items, title_key, organization_key, styles):
    flowables = []
    for item in items or []:
        if not isinstance(item, dict):
            continue

        title = _text(item.get(title_key, ""))
        organization = _text(item.get(organization_key, ""))
        flowables.append(
            Paragraph(
                f"<b>{title}</b><br/><font color='#555555'>{organization}</font>",
                styles["EntryTitle"],
            )
        )

        metadata = _metadata(item)
        if metadata:
            flowables.append(Paragraph(_text(metadata), styles["Meta"]))

        description = item.get("description")
        if description:
            flowables.append(Paragraph(_text(description), styles["Body"]))

        bullet_items = item.get("achievements") or item.get("honors") or []
        if bullet_items:
            flowables.append(
                ListFlowable(
                    [
                        ListItem(Paragraph(_text(value), styles["Body"]))
                        for value in bullet_items
                    ],
                    bulletType="bullet",
                    leftIndent=12,
                )
            )

        flowables.append(Spacer(1, 6))
    return flowables


def _section(title, content, styles):
    if not content:
        return []
    return [
        Paragraph(_text(title).upper(), styles["Section"]),
        HRFlowable(width="100%", thickness=0.7, color=colors.HexColor("#0B9A9A"), spaceAfter=6),
        *content,
    ]


def _resume_story(resume_data, styles):
    personal_info = resume_data.get("personal_info") or {}
    if not isinstance(personal_info, dict):
        personal_info = {"full_name": personal_info}

    name = Paragraph(_text(personal_info.get("full_name", "Resume")), styles["Name"])
    headline = Paragraph(_text(personal_info.get("headline", "")), styles["Headline"])
    contact_values = []
    for field in ("phone", "email", "linkedin", "github", "website"):
        if personal_info.get(field):
            contact_values.append(_text(personal_info[field]))
    address = personal_info.get("address")
    if isinstance(address, dict):
        address_text = ", ".join(
            str(address.get(field))
            for field in ("city", "state", "country")
            if address.get(field)
        )
        if address_text:
            contact_values.append(_text(address_text))

    header = Table(
        [[name, headline], [Paragraph(" | ".join(contact_values), styles["Contact"]), ""]],
        colWidths=[4.1 * inch, 2.75 * inch],
    )
    header.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("SPAN", (0, 1), (1, 1)),
                ("LINEBELOW", (0, 1), (1, 1), 0.8, colors.HexColor("#0B9A9A")),
                ("BOTTOMPADDING", (0, 1), (1, 1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    left = []
    summary = resume_data.get("summary")
    if summary:
        left.extend(_section("Highlights", [Paragraph(_text(summary), styles["Body"])], styles))

    left.extend(
        _section(
            "Work Experience",
            _entry_flowables(resume_data.get("work_experience"), "job_title", "company", styles),
            styles,
        )
    )
    left.extend(
        _section(
            "Education",
            _entry_flowables(resume_data.get("education"), "degree", "institution", styles),
            styles,
        )
    )

    right = []
    skills = resume_data.get("skills") or []
    if skills:
        right.extend(_section("Skills", [Paragraph(_text(", ".join(str(skill) for skill in skills)), styles["Body"])], styles))

    certifications = resume_data.get("certifications") or []
    certificates = [
        ListItem(Paragraph(f"<b>{_text(item.get('title', ''))}</b><br/>{_text(item.get('issuer', ''))}", styles["Body"]))
        for item in certifications
        if isinstance(item, dict)
    ]
    if certificates:
        right.extend(_section("Certificates", [ListFlowable(certificates, bulletType="bullet", leftIndent=12)], styles))

    projects = resume_data.get("projects") or []
    right.extend(
        _section(
            "Projects",
            _entry_flowables(projects, "title", "technologies", styles),
            styles,
        )
    )

    languages = resume_data.get("languages") or []
    language_items = [
        f"<b>{_text(item.get('language', ''))}</b> | {_text(item.get('proficiency', ''))}"
        for item in languages
        if isinstance(item, dict)
    ]
    if language_items:
        right.extend(_section("Languages", [Paragraph("<br/>".join(language_items), styles["Body"])], styles))

 
    return [
    header,
    Spacer(1, 18),

    *left,
    *right,
]


def _resume_section_flowables(section_name, content, styles):
    flowables = []

    if section_name == "work_experience":
        for job in content or []:
            job_title = job.get("job_title", "")
            company = job.get("company", "")

            flowables.append(
                Paragraph(
                    f"<b>{_text(job_title)}</b> | {_text(company)}",
                    styles["JobTitle"],
                )
            )

            location = job.get("location", {})
            city = location.get("city", "") if isinstance(location, dict) else ""

            start_date = job.get("start_date", "")
            end_date = job.get("end_date", "")

            flowables.append(
                Paragraph(
                    f"{_text(city)} | {_text(start_date)} - {_text(end_date)}",
                    styles["Meta"],
                )
            )

            description = job.get("description", "")
            if description:
                flowables.append(
                    Paragraph(_text(description), styles["Body"])
                )

            for achievement in job.get("achievements", []):
                flowables.append(
                    Paragraph(
                        f"• {_text(achievement)}",
                        styles["Body"],
                    )
                )

    elif section_name == "education":
        for education in content or []:
            degree = education.get("degree", "")
            institution = education.get("institution", "")

            flowables.append(
                Paragraph(
                    f"<b>{_text(degree)}</b> | {_text(institution)}",
                    styles["JobTitle"],
                )
            )

            description = education.get("description", "")
            if description:
                flowables.append(
                    Paragraph(_text(description), styles["Body"])
                )

    elif section_name == "skills":
        if isinstance(content, list):
            flowables.append(
                Paragraph(
                    _text(", ".join(str(skill) for skill in content)),
                    styles["Body"],
                )
            )

    else:
        flowables.extend(_content_flowables(content, styles))

    return flowables
def generate_resume_pdf(resume_data):
    """Generate a revised resume in the template's A4 visual style."""
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.7 * inch,
        leftMargin=0.7 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title="Revised Resume",
    )

    base_styles = getSampleStyleSheet()
    styles = {
        "Name": ParagraphStyle(
            "Name",
            parent=base_styles["Title"],
            alignment=TA_LEFT,
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=25,
            textColor=colors.HexColor("#078C95"),
        ),
        "Headline": ParagraphStyle("Headline", parent=base_styles["BodyText"], alignment=TA_LEFT, fontSize=13, leading=16, textColor=colors.HexColor("#333333")),
        "Contact": ParagraphStyle("Contact", parent=base_styles["BodyText"], fontSize=8.5, leading=11, textColor=colors.HexColor("#555555")),
        "EntryTitle": ParagraphStyle("EntryTitle", parent=base_styles["BodyText"], fontSize=9.5, leading=12, spaceBefore=4, spaceAfter=1),
        "Section": ParagraphStyle(
            "Section",
            parent=base_styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=12,
            textColor=colors.HexColor("#078C95"),
            spaceBefore=8,
            spaceAfter=0,
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
        "JobTitle": ParagraphStyle(
            "JobTitle",
            parent=base_styles["BodyText"],
            fontSize=10,
            leading=13,
            spaceBefore=6,
            spaceAfter=2,
        ),
    


        "Meta": ParagraphStyle(
            "Meta",
            parent=base_styles["BodyText"],
            fontSize=8,
            textColor=colors.grey,
            spaceAfter=4,
   ),
    }

    document.build(_resume_story(resume_data or {}, styles))
    return buffer.getvalue()
