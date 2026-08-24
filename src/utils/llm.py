from prompts import (
    RESUME_YAML_SCHEMA,
    LLM_YAML_PARSE_PROMPT,
    RESUME_REVIEW_PROMPT,
    JOB_DESCRIPTION_REVIEW_PROMPT,
    REVIEW_OUTPUT_SCHEMA,
)
from utils.yaml import extract_yaml
from config import GEMINI_API_KEY, LLM_MODEL
from google import genai
from google.genai import types
import streamlit as st


DEFAULT_MODEL = LLM_MODEL


@st.cache_resource
def get_gemini_client():
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set. Add your Gemini API key to the environment.")
    return genai.Client(api_key=GEMINI_API_KEY)


def call_llm(prompt, model=DEFAULT_MODEL):
    response = get_gemini_client().models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction="You are a helpful assistant.",
            temperature=0.2,
        ),
    )
    return response.text


def parse_resume(resume_text):
    parse_prompt = LLM_YAML_PARSE_PROMPT.format(
        resume_schema=RESUME_YAML_SCHEMA, resume_text=resume_text
    )
    resume_yaml = call_llm(parse_prompt)
    return extract_yaml(resume_yaml)


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
    return extract_yaml(review_response)
