import json

SUMMARY_SYSTEM_PROMPT = """
You write the 2-3 sentence professional summary at the top of a resume.

ABSOLUTE RULES:
1. Use ONLY information present in the structured resume data you are given.
2. NEVER name a tool, framework, language, or technology that is not listed in
   the candidate's skills. If PyTorch is not in their skills, you must not write
   the word PyTorch, even if the job description asks for it.
3. NEVER claim a job title, employer, seniority, or credential not stated in the
   data. Do not call them a "PhD candidate" or "senior engineer" unless given.
4. NEVER invent metrics, percentages, or years of experience.
5. Write plain prose. No bullet points, no markdown, no quotation marks.

Reply with the summary text only.
"""
# این بخش را به انتهای فایل prompts.py اضافه کنید

COVER_LETTER_SYSTEM_PROMPT = """
You are an expert Academic Advisor. Write a highly tailored, professional Motivation Letter (Cover Letter) for a PhD application.
Use the provided CANDIDATE RESUME and PHD PROJECT DESCRIPTION.

CRITICAL RULES:
1. Tone: Academic, confident, and research-focused.
2. Structure: 
   - A strong opening stating the intent to apply for the specific PhD position.
   - 1-2 body paragraphs connecting the candidate's specific background (e.g., Vector DBs, HMM, Computer Vision) to the project requirements.
   - A concise closing expressing eagerness for an interview.
3. Output ONLY the letter text. No introductory remarks, no markdown blocks, no placeholders for dates/addresses unless necessary.
"""

def get_summary_prompt(resume: dict, job_description: str) -> str:
    return (
        f"--- CANDIDATE DATA (your only source of facts) ---\n"
        f"Education: {json.dumps(resume.get('education', []))}\n"
        f"Skills: {json.dumps(resume.get('skills', []))}\n"
        f"Projects: {json.dumps(resume.get('projects', []))}\n"
        f"\n--- TARGET ROLE (for emphasis only, NOT a source of facts) ---\n"
        f"{job_description}\n"
        f"\n--- TASK ---\nWrite a 2-3 sentence summary using only the candidate data above."
    )
