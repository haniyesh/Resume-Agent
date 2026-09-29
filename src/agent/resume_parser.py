"""Deterministic resume parser.

The LLM is unreliable at extracting facts (it invents skills and drops real
ones), so every factual field is parsed here with regexes. The LLM is only ever
used to write the summary, and its output is discarded if it mentions anything
that does not appear in the source resume.
"""

import re
from typing import Optional

SKILL_HEADINGS = (
    "technical skills", "core skills", "skills", "core competencies",
    "competencies", "technologies", "technical proficiencies",
    "programming languages", "tools",
)

EDUCATION_HEADINGS = (
    "education", "academic background", "academic qualifications", "qualifications",
)

PROJECT_HEADINGS = (
    "research & projects", "research and projects", "relevant projects",
    "projects", "experience", "work experience", "professional experience",
    "employment", "research experience",
)

SUMMARY_HEADINGS = (
    "professional summary", "summary", "profile", "about", "objective",
)

_SECTION_RE = re.compile(r"^([A-Z][A-Za-z &/,'()-]{2,40}):?\s*$")

_SECTION_WORDS = (
    "summary", "profile", "about", "objective",
    "skill", "competenc", "technolog", "tool", "programming language",
    "education", "academic", "degree",
    "project", "research", "experience", "work", "employment",
    "publication", "certification", "award", "honor", "language",
)


def _is_heading(line: str) -> bool:
    if not _SECTION_RE.match(line):
        return False
    if line == line.upper():
        return True
    if line.endswith("."):
        return False
    lowered = line.lower()
    return any(word in lowered for word in _SECTION_WORDS)


def _sections(text: str) -> dict[str, list[str]]:
    """Splits a resume into heading -> body lines. Handles ALL-CAPS and Title Case."""
    found: dict[str, list[str]] = {}
    current: Optional[str] = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if _is_heading(line):
            current = line.rstrip(":").strip()
            found.setdefault(current, [])
            continue
        if current:
            found[current].append(line)
    return found


def _match_section(sections: dict[str, list[str]], headings: tuple[str, ...]) -> list[str]:
    for heading, body in sections.items():
        if heading.lower().rstrip(":") in headings:
            return body
    return []


def parse_skills(body: list[str]) -> list[str]:
    """Handles 'Category: a, b, c', 'a • b • c', and bare list formats."""
    skills: list[str] = []
    for line in body:
        line = re.sub(r"^[-*\u2022]\s*", "", line).strip()
        if ":" in line:
            _, _, rest = line.partition(":")
            line = rest
        for item in re.split(r"[,;|]|\s[-–—]\s|[\u2022\u25cf\u25aa]", line):
            item = item.strip(" .*-")
            if item and item not in skills:
                skills.append(item)
    return skills


def parse_education(body: list[str]) -> list[dict]:
    entries = []
    current: Optional[dict] = None
    details: list[str] = []

    for line in body:
        line = re.sub(r"^[-*\u2022]\s*", "", line)
        if re.match(r"^(Master|Bachelor|Ph\.?D|Doctorate|B\.?Sc|M\.?Sc|MSc|BSc|Associate|MBA)", line, re.I):
            if current:
                current["details"] = " | ".join(details).strip(" |")
                entries.append(current)
            current = {"degree": line, "institution": "", "details": ""}
            details = []
        elif current:
            if re.search(r"universit|institute|college|school|academy", line, re.I):
                current["institution"] = line
            else:
                details.append(line)

    if current:
        current["details"] = " | ".join(details).strip(" |")
        entries.append(current)
    return entries


_MD_RE = re.compile(r"[*_`]+")


def _clean(text: str) -> str:
    """Strips markdown emphasis and leading bullet markers."""
    return _MD_RE.sub("", text).strip(" -*•\u2022")


def _is_project_title(line: str) -> bool:
    """A short, title-cased, colon-free line that does not end in a period."""
    if line.endswith((".", ",", ";", ":")) or ":" in line:
        return False
    words = line.split()
    if not 1 <= len(words) <= 8:
        return False
    return sum(1 for w in words if w[:1].isupper()) >= max(1, len(words) - 1)


def parse_projects(body: list[str]) -> list[dict]:
    projects: list[dict] = []
    current: Optional[dict] = None

    for raw in body:
        line = raw.strip()
        is_bullet = bool(re.match(r"^[-*\u2022]", line))
        text = _clean(line)

        if is_bullet and "|" in text:
            title, _, org = text.partition("|")
            if current is not None:
                projects.append(current)
            current = {"title": f"{title.strip()} - {org.strip()}", "description": []}
            continue

        if is_bullet:
            if current is None:
                current = {"title": "", "description": [text]}
            else:
                current["description"].append(text)
            continue

        if current is None or not current["description"]:
            if current is not None:
                current["description"].append(text)
            else:
                current = {"title": text, "description": []}
            continue

        if _is_project_title(text):
            projects.append(current)
            current = {"title": text, "description": []}
        else:
            current["description"].append(text)

    if current is not None:
        projects.append(current)

    return [p for p in projects if p["title"] or p["description"]]


def parse_header(text: str, sections: dict[str, list[str]]) -> dict:
    """Name/contact come from the lines above the first heading.

    Falls back to the existing summary when the resume has no name line.
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    header_lines: list[str] = []
    for line in lines:
        if _is_heading(line):
            break
        header_lines.append(line)

    name = ""
    contact_parts: list[str] = []
    for line in header_lines:
        if "|" in line or "@" in line or re.search(r"https?://|www\.", line):
            contact_parts.extend(p.strip() for p in re.split(r"[|•]", line) if p.strip())
        elif not name and not _is_heading(line):
            name = line
        elif name:
            contact_parts.append(line)

    if not contact_parts and (not name or len(name) > 60 or name.endswith(".")):
        for heading, body in sections.items():
            if heading.lower() in SUMMARY_HEADINGS and body:
                name = ""

    return {"name": name, "contact": " | ".join(contact_parts)}


def parse_resume(text: str) -> dict:
    sections = _sections(text)
    header = parse_header(text, sections)
    return {
        "name": header["name"],
        "contact": header["contact"],
        "skills": parse_skills(_match_section(sections, SKILL_HEADINGS)),
        "projects": parse_projects(_match_section(sections, PROJECT_HEADINGS)),
        "education": parse_education(_match_section(sections, EDUCATION_HEADINGS)),
    }
