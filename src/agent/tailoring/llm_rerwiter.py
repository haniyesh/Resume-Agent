import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the OpenAI client
# It automatically looks for the OPENAI_API_KEY in your environment variables
client = OpenAI(base_url=os.getenv("OLLAMA_BASE_URL"), api_key=os.getenv("OLLAMA_API_KEY"))

def tailor_resume(raw_resume: str, job_description: str) -> dict:
    """
    Advanced Version: Takes the raw resume and a job description, uses OpenAI API,
    and returns a tailored resume EXACTLY in JSON format (ready for PDF generation).
    """
    
    # =====================================================================
    # 📝 SYSTEM PROMPT (Engineered for Structured Output & Chain of Thought)
    # =====================================================================
    SYSTEM_PROMPT = """
    You are an Expert AI IT Recruiter. Your task is to tailor a candidate's resume to perfectly match the provided Job Description.
    
    CRITICAL RULES:
    1. DO NOT invent or fabricate any skills, jobs, or degrees the candidate does not have.
    2. Focus on rewriting the existing experience bullet points to highlight skills mentioned in the Job Description.
    3. You MUST return the output EXACTLY as a JSON object, following the schema below.
    
    JSON SCHEMA:
    {
        "reasoning": "First, briefly analyze what the job needs and what the candidate has. Write your thought process here.",
        "professional_summary": "A 3-sentence summary tailored to the job.",
        "core_skills": ["skill1", "skill2", "skill3"],
        "experience": [
            {
                "job_title": "Original Title",
                "company": "Original Company",
                "tailored_bullet_points": [
                    "Action verb + what they did + impact (tailored to job).",
                    "..."
                ]
            }
        ]
    }
    """
    
    USER_PROMPT = f"""
    --- JOB DESCRIPTION ---
    {job_description}
    
    --- ORIGINAL RESUME ---
    {raw_resume}
    """

    try:
        print("[LLM] 🧠 Sending request to OpenAI API (please wait)...")
        
        response = client.chat.completions.create(
            # Using gpt-4o-mini is highly recommended here: it's incredibly fast, very cheap, and smart enough for JSON.
            model="gpt-4o-mini",
            
            # 💡 THE MAGIC: This forces OpenAI's API to return a valid JSON object.
            # NOTE: When using this, your SYSTEM_PROMPT *must* explicitly contain the word "JSON".
            response_format={ "type": "json_object" },
            
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT}
            ],
            
            # 💡 Low temperature = High precision (no hallucinations/lies on the resume)
            temperature=0.1,
            max_tokens=2500
        )
        
        # Extract the raw string response
        raw_json_string = response.choices[0].message.content
        
        # Convert the JSON string into a Python dictionary
        tailored_data = json.loads(raw_json_string)
        
        return tailored_data

    except json.JSONDecodeError:
        print("❌ [Error] OpenAI failed to return a valid JSON.")
        return {}
    except Exception as e:
        print(f"❌ [Error] API Call Failed: {e}")
        return {}

# --- Debugging / Testing Block ---
if __name__ == "__main__":
    sample_resume = """
    Experience:
    - Data Scientist at TechCorp (2020-2023): Built predictive models using Python, scikit-learn, and SQL. 
    - AI Intern at StartupX (2019): Worked on simple object detection with OpenCV.
    """
    sample_job = """
    We need an AI Vision Engineer. Must have strong Python skills and experience with Computer Vision, Object Detection, and YOLO.
    SQL is a plus but not required.
    """
    
    if not os.getenv("adzuna_app_key"):
        print("⚠️ Warning: No ADZUNA_APP_KEY found in .env file. The test will fail.")
    else:
        result = tailor_resume(sample_resume, sample_job)
        
        print("\n✅ --- FINAL OUTPUT (Python Dictionary) ---")
        # Pretty-print the JSON output
        print(json.dumps(result, indent=4, ensure_ascii=False))