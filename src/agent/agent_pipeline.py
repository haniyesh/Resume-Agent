import os
import re
import sys
import json
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

SRC_ROOT = Path(__file__).resolve().parent.parent
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from agent.resume_parser import parse_resume
from agent.tailoring.pdf_parser import extract_text_from_pdf, clean_resume_text
from agent.tailoring.pdf_generator import generate_tailored_pdf
from config.prompts import SUMMARY_SYSTEM_PROMPT, get_summary_prompt

load_dotenv()

client = OpenAI(
    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434") + "/v1",
    api_key="ollama",
)
MODEL = os.getenv("LLM_MODEL", "llama3.2:3b")

# =================================================================
# Helpers
# =================================================================
def load_resume_text(path: str) -> str:
    if path.lower().endswith(".pdf"):
        return clean_resume_text(extract_text_from_pdf(path))
    return clean_resume_text(Path(path).read_text(encoding="utf-8"))


def _jd_keywords(job_description: str) -> set[str]:
    stop = {
        "the", "and", "with", "for", "from", "you", "our", "are", "will", "have",
        "this", "that", "job", "role", "team", "work", "years", "plus", "strong",
        "experience", "using", "including", "such", "able", "across", "into",
        "who", "them", "they", "must", "should", "not", "but", "all", "their",
    }
    words = re.findall(r"[A-Za-z][A-Za-z0-9+#.-]{2,}", job_description.lower())
    return {w for w in words if w not in stop}


def _rank_by_job(items: list, job_description: str, key) -> list:
    """Reorders existing items toward the job. Never adds or removes any."""
    keywords = _jd_keywords(job_description)
    return sorted(
        items,
        key=lambda item: (
            -len(set(re.findall(r"[a-z0-9+#.]+", key(item).lower())) & keywords),
            items.index(item),
        ),
    )


def _summary_is_grounded(summary: str, resume_text: str) -> bool:
    """Rejects a summary naming a capitalized term absent from the resume.

    Only mid-sentence capitalized words are checked; a capitalized first word is
    ordinary sentence casing ("Highly skilled..."), not a claim.
    """
    resume_lower = resume_text.lower()
    for sentence in re.split(r"(?<=[.!?])\s+", summary):
        for word in sentence.split()[1:]:
            word = word.strip(".,;:()")
            if not re.fullmatch(r"[A-Z][A-Za-z0-9+#]{2,}", word):
                continue
            if word.lower() not in resume_lower:
                return False
    return True


def _fallback_summary(resume: dict) -> str:
    parts = []
    if resume["education"]:
        parts.append(resume["education"][0]["degree"])
    if resume["skills"]:
        parts.append("Skills: " + ", ".join(resume["skills"][:6]))
    if resume["projects"]:
        parts.append("Projects: " + ", ".join(p["title"] for p in resume["projects"]))
    return ". ".join(parts) + "."


def write_summary(resume: dict, resume_text: str, job_description: str) -> str:
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                {"role": "user", "content": get_summary_prompt(resume, job_description)},
            ],
            temperature=0.2,
        )
        summary = response.choices[0].message.content.strip().strip('"')
    except Exception as e:
        print(f"⚠️ خلاصه‌سازی ناموفق بود ({e}); از نسخهٔ خودکار استفاده شد.")
        return _fallback_summary(resume)

    if not _summary_is_grounded(summary, resume_text):
        print("⚠️ خلاصهٔ مدل شامل مواردی خارج از رزومه بود؛ از نسخهٔ خودکار استفاده شد.")
        return _fallback_summary(resume)

    return summary


# =================================================================
# Pipeline
# =================================================================
def run_pipeline(resume_path: str, job_description: str, output_filename: str) -> bool:
    print("🚀 [Pipeline] شروع پایپ‌لاین تنظیم رزومه...")

    resume_text = load_resume_text(resume_path)
    if not resume_text:
        print("❌ [Pipeline Error] متن رزومه خالی است. پایپ‌لاین متوقف شد.")
        return False

    print("📋 [Pipeline] استخراج واقعیت‌ها از رزومه (بدون مدل)...")
    resume = parse_resume(resume_text)
    if not resume["skills"] and not resume["projects"]:
        print("❌ [Pipeline Error] هیچ مهارت یا پروژه‌ای پارس نشد. پایپ‌لاین متوقف شد.")
        return False
    print(
        f"   نام={resume['name']!r} مهارت‌ها={len(resume['skills'])} "
        f"پروژه‌ها={len(resume['projects'])} تحصیلات={len(resume['education'])}"
    )

    print("✍️ [Pipeline] نوشتن خلاصه...")
    summary = write_summary(resume, resume_text, job_description)

    tailored = {
        "name": resume["name"],
        "contact": resume["contact"],
        "summary": summary,
        "skills": _rank_by_job(resume["skills"], job_description, lambda s: s),
        "projects": _rank_by_job(
            resume["projects"], job_description, lambda p: json.dumps(p, ensure_ascii=False)
        ),
        "education": resume["education"],
    }

    print("📊 [Pipeline] رندر کردن PDF نهایی...")
    generate_tailored_pdf(tailored, output_filename)
    return True


def main():
    data_dir = Path(__file__).resolve().parent.parent / "data"
    default_resume = data_dir / "resume.txt"
    if not default_resume.exists():
        default_resume = data_dir / "test_resume.pdf"
    resume_path = os.getenv("RESUME_PATH", str(default_resume))
    jobs_json_path = os.getenv("JOBS_JSON_PATH", str(data_dir / "phd_positions.json"))

    if not os.path.exists(resume_path) or not os.path.exists(jobs_json_path):
        print("⚠️ فایل رزومه یا فایل JSON پوزیشن‌ها پیدا نشد. مسیر data را بررسی کنید.")
        return

    print("🚀 شروع اجرای خودکار (Batch Processing)...")
    with open(jobs_json_path, "r", encoding="utf-8") as file:
        phd_list = json.load(file)

    succeeded = 0
    for job in phd_list:
        clean_uni_name = job["university"].replace(" ", "_").replace("/", "-")
        output_name = f"Haniye_CV_{clean_uni_name}.pdf"

        print(f"\n{'=' * 50}")
        print(f"🎯 هدف: {job['title']} در {job['university']}")

        if run_pipeline(resume_path, job["description"], output_name):
            succeeded += 1

    print(f"\n{'=' * 50}")
    print(f"🎉 عملیات موفق! {succeeded}/{len(phd_list)} رزومه تولید شد.")


if __name__ == "__main__":
    main()
