"""Resume tailoring pipeline: PDF in -> LLM-tailored PDF out."""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

SRC_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SRC_DIR / "data"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

load_dotenv(SRC_DIR.parent / ".env")

from agent.tailoring.pdf_generator import generate_resume_pdf
from agent.tailoring.llm_matcher import tailor_resume_with_llm
from agent.tailoring.pdf_parser import clean_resume_text, extract_text_from_pdf

FALLBACK_JOB_DESCRIPTION = """
We are looking for an AI Engineer / Python Developer.
Requirements:
- Strong background in Python, Git, and automated scripts.
- Experience with local LLMs, Ollama, or OpenAI APIs.
- Familiarity with vector databases and data parsing.
"""


def load_job_description() -> str:
    """Return the job description from JOB_DESCRIPTION_PATH, sample_job.txt, or a fallback."""
    configured = os.getenv("JOB_DESCRIPTION_PATH")
    if configured:
        if not os.path.exists(configured):
            print(f"[Pipeline Error] Job description not found at path: {configured}")
            return ""
        return Path(configured).read_text(encoding="utf-8").strip()

    sample_job = DATA_DIR / "sample_job.txt"
    if sample_job.exists():
        return sample_job.read_text(encoding="utf-8").strip()

    return FALLBACK_JOB_DESCRIPTION.strip()


def run_resume_pipeline() -> str:
    """Tailor the base resume against the job description and return the output PDF path."""
    print("🚀 [Pipeline] Starting Resume Tailoring Pipeline...")

    resume_pdf_path = os.getenv("RESUME_PDF_PATH") or str(DATA_DIR / "resume.pdf")
    if not os.path.exists(resume_pdf_path):
        print(f"❌ [Pipeline Error] Resume PDF not found at path: {resume_pdf_path}")
        return ""

    job_description = load_job_description()
    if not job_description:
        return ""

    print(f"📄 [Pipeline] Reading base resume from '{resume_pdf_path}'...")
    raw_resume_text = extract_text_from_pdf(resume_pdf_path)
    if not raw_resume_text:
        print("❌ [Pipeline Error] Extracted resume text is empty. Pipeline stopped.")
        return ""

    resume_text = clean_resume_text(raw_resume_text)
    print(f"   [Pipeline] Extracted {len(resume_text)} characters of resume text.")

    print("🤖 [Pipeline] Sending data to LLM (Ollama) for tailoring...")
    tailored_json_data = tailor_resume_with_llm(resume_text, job_description)

    if not tailored_json_data or "error" in tailored_json_data:
        detail = tailored_json_data.get("error", "empty response") if tailored_json_data else "empty response"
        print(f"❌ [Pipeline Error] LLM failed to return valid data ({detail}). Pipeline stopped.")
        return ""

    print("✅ [Pipeline] Tailored JSON received successfully:")
    print(json.dumps(tailored_json_data, indent=2, ensure_ascii=False))

    output_pdf_path = os.getenv("OUTPUT_PDF_PATH") or str(DATA_DIR / "Haniye_Tailored_Resume.pdf")
    print(f"📊 [Pipeline] Generating final PDF resume as '{output_pdf_path}'...")

    generate_resume_pdf(tailored_json_data, output_filename=output_pdf_path)

    print("🎉 [Pipeline] Pipeline finished successfully! Your tailored resume is ready.")
    return output_pdf_path


if __name__ == "__main__":
    run_resume_pipeline()
