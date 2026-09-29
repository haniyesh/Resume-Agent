import os
import json
from dotenv import load_dotenv
from agent.tailoring.pdf_parser import extract_text_from_pdf, clean_resume_text
from config import tailor_resume_with_llm
from agent.tailoring.pdf_generator import generate_resume_pdf


load_dotenv()

def run_resume_pipeline():
    print("🚀 [Pipeline] Starting Resume Tailoring Pipeline...")

    resume_pdf_path = os.getenv("RESUME_PDF_PATH", "../../data/resume.pdf")
    if not os.path.exists(resume_pdf_path):
        print(f"❌ [Pipeline Error] Resume PDF not found at path: {resume_pdf_path}")
        return
    
    job_description = """
    We are looking for a Junior AI Engineer with strong Python skills.
    Requirements:
    - Experience with Python and PyTorch or TensorFlow.
    - Familiarity with Local LLMs, Ollama, or OpenAI APIs.
    - Good understanding of software engineering best practices, Git, and FastAPI.
    - Ability to work with vector databases is a big plus.
    """

    print(f"📄 [Pipeline] Reading base resume from '{resume_pdf_path}'...")
    raw_resume_text = extract_text_from_pdf(resume_pdf_path)
    if not raw_resume_text:
        print("❌ [Pipeline Error] Extracted resume text is empty. Pipeline stopped.")
        return

    job_description = """
    We are looking for an AI Engineer / Python Developer.
    Requirements:
    - Strong background in Python, Git, and automated scripts.
    - Experience with local LLMs, Ollama, or OpenAI APIs.
    - Familiarity with vector databases and data parsing.
    """

    print("🤖 [Pipeline] Sending data to LLM (Ollama) for tailoring...")
    tailored_json_data = tailor_resume_with_llm(raw_resume_text, job_description)

    if not tailored_json_data:
        print("❌ [Pipeline Error] LLM failed to return valid data. Pipeline stopped.")
        return

    print("✅ [Pipeline] Tailored JSON received successfully:")
    print(json.dumps(tailored_json_data, indent=2, ensure_ascii=False))

    # Generate final tailored PDF resume
    output_pdf_name = "Haniye_Tailored_Resume.pdf"
    print(f"📊 [Pipeline] Generating final PDF resume as '{output_pdf_name}'...")
    
    generate_resume_pdf(tailored_json_data, output_filename=output_pdf_name)

    print("🎉 [Pipeline] Pipeline finished successfully! Your tailored resume is ready.")

    if __name__ == "__main__":
        run_resume_pipeline()