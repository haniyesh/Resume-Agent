import requests
import yaml
from prompts import (
    RESUME_YAML_SCHEMA,
    LLM_YAML_PARSE_PROMPT,
    RESUME_REVIEW_PROMPT,
    JOB_DESCRIPTION_REVIEW_PROMPT,
    JOB_TITLES_PROMPT,
    REVIEW_OUTPUT_SCHEMA,
    YAML_REPAIR_PROMPT,
)
from utils.yaml import extract_yaml, repair_yaml
from config import OLLAMA_BASE_URL, LLM_MODEL


DEFAULT_MODEL = LLM_MODEL


def call_llm(prompt, model=DEFAULT_MODEL):
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "options": {"temperature": 0.2},
        },
        timeout=300,
    )
    response.raise_for_status()
    return response.json()["message"]["content"]


def parse_resume(resume_text):
    parse_prompt = LLM_YAML_PARSE_PROMPT.format(
        resume_schema=RESUME_YAML_SCHEMA, resume_text=resume_text
    )
    return _validated_yaml(call_llm(parse_prompt))


def _validated_yaml(raw, retries=2):
    """Return YAML text only if it parses; otherwise ask the model to repair it."""
    cleaned = extract_yaml(raw)
    try:
        yaml.safe_load(cleaned)
    except yaml.YAMLError as exc:
        repaired = repair_yaml(cleaned)
        if repaired is not None:
            return repaired
        if retries <= 0:
            raise ValueError(f"Invalid YAML after repair retries: {exc}") from exc
        llm_repaired = call_llm(
            YAML_REPAIR_PROMPT.format(error=exc, invalid_yaml=cleaned)
        )
        return _validated_yaml(llm_repaired, retries - 1)
    return cleaned


def extract_job_titles(resume_text, max_titles=10):
    """Extract a list of job titles from resume text via the LLM."""
    prompt = JOB_TITLES_PROMPT.format(max_titles=max_titles, resume_text=resume_text)
    raw = _validated_yaml(call_llm(prompt))
    data = yaml.safe_load(raw)
    if not isinstance(data, list):
        return []
    return [str(title).strip() for title in data if str(title).strip()]


def review_resume(resume_yaml, job_description=None):
    if job_description:
        review_prompt = JOB_DESCRIPTION_REVIEW_PROMPT.format(
            resume_data=resume_yaml,
            job_description=job_description,
            review_output_schema=REVIEW_OUTPUT_SCHEMA,
        )
    else:
        review_prompt = RESUME_REVIEW_PROMPT.format(
            resume_data=resume_yaml, review_output_schema=REVIEW_OUTPUT_SCHEMA
        )

    review_response = call_llm(review_prompt)
    return _validated_yaml(review_response)