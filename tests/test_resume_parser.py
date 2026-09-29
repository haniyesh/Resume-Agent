import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agent.resume_parser import parse_resume
from agent.agent_pipeline import _summary_is_grounded, _rank_by_job, load_resume_text
from agent.tailoring.pdf_generator import safe_text

RESUME = """Haniye Shakibayi Senobari
Istanbul, Turkiye | haniye.sh@email.com | linkedin.com/in/haniye

EDUCATION
Master of Science in Artificial Intelligence
Bahcesehir University, Istanbul, Turkiye
GPA: 3.50
Thesis Focus: Uncertainty-aware few-shot user adaptation.

TECHNICAL SKILLS
Programming Languages: Python, Pine Script, MQL5
Artificial Intelligence: YOLO (Object Detection), Hidden Markov Models (HMM)

RESEARCH & PROJECTS
Financial Market Regime Detection
- Applied Hidden Markov Models to identify market stress.

Cognitive Safety Agent & Computer Vision
- Implemented YOLO-based models with Qdrant.
"""


@pytest.fixture
def parsed():
    return parse_resume(RESUME)


def test_extracts_name_and_contact(parsed):
    assert parsed["name"] == "Haniye Shakibayi Senobari"
    assert "haniye.sh@email.com" in parsed["contact"]
    assert "Istanbul, Turkiye" in parsed["contact"]


def test_extracts_all_skills_without_inventing(parsed):
    assert parsed["skills"] == [
        "Python",
        "Pine Script",
        "MQL5",
        "YOLO (Object Detection)",
        "Hidden Markov Models (HMM)",
    ]


def test_splits_multiple_projects(parsed):
    titles = [p["title"] for p in parsed["projects"]]
    assert titles == [
        "Financial Market Regime Detection",
        "Cognitive Safety Agent & Computer Vision",
    ]
    assert len(parsed["projects"][0]["description"]) == 1
    assert len(parsed["projects"][1]["description"]) == 1


def test_preserves_education_details(parsed):
    assert len(parsed["education"]) == 1
    edu = parsed["education"][0]
    assert edu["degree"] == "Master of Science in Artificial Intelligence"
    assert "Bahcesehir University" in edu["institution"]
    assert "GPA: 3.50" in edu["details"]
    assert "Thesis Focus" in edu["details"]


def test_parses_title_case_headings():
    text = (
        "Jane Doe\njane@example.com\n\n"
        "Professional Summary\nEngineer.\n\n"
        "Core Skills\nPython - FastAPI - Ollama\n\n"
        "Professional Experience\n**AI Developer** | *Lab*\n- Built LLM pipelines.\n"
    )
    result = parse_resume(text)
    assert result["name"] == "Jane Doe"
    assert result["skills"] == ["Python", "FastAPI", "Ollama"]
    assert result["projects"][0]["title"] == "AI Developer - Lab"


def test_ranking_never_adds_or_removes_skills(parsed):
    ranked = _rank_by_job(parsed["skills"], "We need PyTorch and Pine Script.", lambda s: s)
    assert sorted(ranked) == sorted(parsed["skills"])


def test_ranking_promotes_job_relevant_skills(parsed):
    ranked = _rank_by_job(parsed["skills"], "Experience with Pine Script required.", lambda s: s)
    assert ranked[0] == "Pine Script"


def test_summary_rejects_invented_tool():
    assert not _summary_is_grounded(
        "Strong background in Python and PyTorch for production systems.", RESUME
    )


def test_summary_allows_sentence_initial_capitals():
    assert _summary_is_grounded(
        "Highly skilled engineer with strong Python and Pine Script skills.", RESUME
    )


def test_summary_allows_grounded_terms():
    assert _summary_is_grounded(
        "Engineer focused on Hidden Markov Models and YOLO detection.", RESUME
    )


def test_safe_text_folds_unicode_to_latin1():
    assert safe_text("AI — LLM’s “test” …") == "AI - LLM's \"test\" ..."
    assert safe_text("Ünïcodé").encode("latin-1")


def test_load_resume_text_handles_txt(tmp_path):
    path = tmp_path / "r.txt"
    path.write_text(RESUME, encoding="utf-8")
    assert "Haniye" in load_resume_text(str(path))
