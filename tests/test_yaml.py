import os
import sys

import yaml
from io import BytesIO

from PyPDF2 import PdfReader

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from src.resume_formatter import format_resume
from src.utils.yaml import extract_yaml, repair_yaml
from src.utils.resume_pdf import merge_revised_resume, generate_resume_pdf
from src.utils.llm import _validated_yaml
from src.utils import llm as llm_module


def test_extract_yaml_removes_undefined_aliases():
    content = '''
```yaml
experience:
  - company: Acme
    jobs:
      - *job1:
          title: Senior Engineer
          years: 2022-2024
```
'''

    cleaned = extract_yaml(content)
    loaded = yaml.safe_load(cleaned)

    assert loaded["experience"][0]["jobs"][0]["job1"]["title"] == "Senior Engineer"


def test_format_resume_handles_string_personal_info():
    content = {"personal_info": "Jane Doe"}

    rendered = format_resume(content)

    assert "Jane Doe" in rendered


def test_merge_revised_resume_adds_missing_skills_while_keeping_original():
    resume = {"skills": ["Python", "SQL"]}
    review = {"skills": {"impact_level": "High", "revised_content": ["SQL", "FastAPI"]}}

    merged = merge_revised_resume(resume, review)

    assert merged["skills"] == ["Python", "SQL", "FastAPI"]


def test_merge_revised_resume_handles_block_scalar_skills():
    resume = {"skills": ["Python"]}
    review = {
        "skills": {
            "impact_level": "High",
            "revised_content": '    - "Python"\n    - "Docker"\n',
        }
    }

    merged = merge_revised_resume(resume, review)

    assert merged["skills"] == ["Python", "Docker"]


def test_merge_revised_resume_ignores_non_dict_review_section():
    resume = {"skills": ["Python"], "summary": "Hello"}
    review = {"summary": "not a mapping"}

    merged = merge_revised_resume(resume, review)

    assert merged["summary"] == "Hello"
    assert merged["skills"] == ["Python"]


def test_resume_pdf_renders_tail_sections():
    data = {
        "personal_info": {"full_name": "Jane Doe"},
        "volunteer_experience": [
            {"role": "Mentor", "organization": "Code.org", "description": "Mentored students"}
        ],
        "interests": ["Hiking", "Chess"],
        "references": [
            {"name": "Al Smith", "relationship": "Manager", "contact_info": {"email": "al@x.com"}}
        ],
    }

    pdf = generate_resume_pdf(data)
    reader = PdfReader(BytesIO(pdf))
    text = "".join(page.extract_text() for page in reader.pages).upper()

    for section in ("VOLUNTEER EXPERIENCE", "INTERESTS", "REFERENCES"):
        assert section in text


def test_resume_pdf_skips_sections_without_real_content():
    data = {
        "personal_info": {"full_name": "Jane Doe"},
        "summary": "null",
        "volunteer_experience": [
            {"role": None, "organization": None, "location": {"city": None, "state": None},
             "start_date": None, "end_date": None, "description": None}
        ],
        "interests": [None],
        "references": [
            {"name": None, "relationship": None, "contact_info": {"phone": None, "email": None}}
        ],
        "certifications": [{"title": None, "issuer": None}],
        "languages": [{"language": None, "proficiency": "null"}],
    }

    pdf = generate_resume_pdf(data)
    reader = PdfReader(BytesIO(pdf))
    text = "".join(page.extract_text() for page in reader.pages).upper()

    for section in ("HIGHLIGHTS", "VOLUNTEER EXPERIENCE", "INTERESTS", "REFERENCES",
                    "CERTIFICATES", "LANGUAGES"):
        assert section not in text, f"{section} heading must not render for phantom data"
    assert "Python" not in text


def test_resume_pdf_drops_null_language_proficiency():
    data = {
        "personal_info": {"full_name": "Jane Doe"},
        "languages": [{"language": "English", "proficiency": "null"}],
    }

    pdf = generate_resume_pdf(data)
    reader = PdfReader(BytesIO(pdf))
    text = "".join(page.extract_text() for page in reader.pages).upper()

    assert "LANGUAGES" in text
    assert "ENGLISH" in text
    assert "| NULL" not in text


def test_validated_yaml_asks_model_to_repair_then_succeeds():
    bad = '```yaml\njob_title: "Research Project A\nskills: []\n```'
    good = "```yaml\nskills:\n  - \"Python\"\n```"

    calls = []
    original = llm_module.call_llm
    llm_module.call_llm = lambda prompt: calls.append(prompt) or good
    try:
        result = _validated_yaml(bad)
    finally:
        llm_module.call_llm = original

    assert len(calls) == 1
    assert yaml.safe_load(result) == {"skills": ["Python"]}


def test_repair_yaml_dedents_key_after_block_sequence():
    bad = (
        'work_experience:\n'
        '  - job_title: "Research Project A"\n'
        '    company: "University"\n'
        '    achievements:\n'
        '      - "Published a paper"\n'
        '  skills: []\n'
        '  interests:\n'
        '    - "Hiking"\n'
    )

    repaired = repair_yaml(bad)

    assert repaired is not None
    loaded = yaml.safe_load(repaired)
    assert loaded["work_experience"][0]["job_title"] == "Research Project A"
    assert loaded["skills"] == []
    assert loaded["interests"] == ["Hiking"]


def test_validated_yaml_repairs_indentation_without_calling_model():
    bad = (
        '```yaml\n'
        'work_experience:\n'
        '  - job_title: "Research Project A"\n'
        '  skills: []\n'
        '```'
    )

    calls = []
    original = llm_module.call_llm
    llm_module.call_llm = lambda prompt: calls.append(prompt)
    try:
        result = _validated_yaml(bad)
    finally:
        llm_module.call_llm = original

    assert calls == []
    assert yaml.safe_load(result) == {
        "work_experience": [{"job_title": "Research Project A"}],
        "skills": [],
    }


def test_validated_yaml_raises_when_repair_keeps_failing():
    bad = "a:\n  - [unclosed"

    original = llm_module.call_llm
    llm_module.call_llm = lambda prompt: bad
    try:
        try:
            _validated_yaml(bad)
            raise AssertionError("expected ValueError after failed repairs")
        except ValueError:
            pass
    finally:
        llm_module.call_llm = original
