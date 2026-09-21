from io import BytesIO
from typing import Optional, TypedDict, List
import yaml
from utils.pdf import extract_text_from_pdf
from utils.llm import parse_resume, review_resume, extract_job_titles as extract_titles_from_text
from utils.resume_pdf import generate_resume_pdf, merge_revised_resume
from utils.search_jobs import search_jobs as adzuna_search_jobs
from langgraph.graph import StateGraph, START, END

#inpute:resume_pdf:bytes
class AgentState(TypedDict):
  pdf_bytes: bytes
  resume_text: str #stage_1 output
  resume_yaml: str #stage_2 output
  resume_data: dict               # stage 2 parsed (dict)
  job_description: Optional[str]
  job_query: Optional[str]
  job_location: Optional[str]
  jobs: List[dict]                # stage 2b output
  job_count: Optional[int]
  review_data: dict               # stage 3 output
  revised_resume: dict            # stage 4 input
  pdf_output: bytes               # stage 4 output

  errors: List[str]
# define nodes  
def extract_text(state: AgentState) -> dict:
  return { "resume_text": extract_text_from_pdf(state["pdf_bytes"]) }

#input:resume_text, output:resume_yaml
def parse(state: AgentState) -> dict:
  resume_yaml =parse_resume(state["resume_text"])
  return { "resume_yaml": resume_yaml, "resume_data": yaml.safe_load(resume_yaml)  }


#stage 2b: search for jobs on Adzuna
def search_jobs(state: AgentState) -> dict:
    query = state.get("job_query")
    if not query:
        return {}
    result = adzuna_search_jobs(query, location=state.get("job_location"))
    jobs = result["results"]
    updates = {"jobs": jobs, "job_count": result["count"]}
    if not state.get("job_description") and jobs:
        best = jobs[0]
        updates["job_description"] = (
            f"Position: {best['title']}\nCompany: {best['company']}\n"
            f"{best['description']}"
        )
    return updates


#stage 3: review resume
def review(state: AgentState) -> dict:
    review_yaml = review_resume(state["resume_yaml"], state.get("job_description"))
    return {"review_data": yaml.safe_load(review_yaml)}


def merge_and_build_pdf(state: AgentState) -> dict:
    revised = merge_revised_resume(state["resume_data"], state["review_data"])
    return {"revised_resume": revised, "pdf_output": generate_resume_pdf(revised)}


#------ EDGES

_builder = StateGraph(AgentState)
_builder.add_node("extract_text", extract_text)
_builder.add_node("parse", parse)
_builder.add_node("search_jobs", search_jobs)
_builder.add_node("review_resume", review)
_builder.add_node("merge_and_build_pdf", merge_and_build_pdf)


_builder.add_edge(START, "extract_text")
_builder.add_edge("extract_text", "parse")
_builder.add_edge("parse", "review_resume")
_builder.add_edge(START, "search_jobs")
_builder.add_edge("search_jobs", "review_resume")
_builder.add_edge("review_resume", "merge_and_build_pdf")
_builder.add_edge("merge_and_build_pdf", END)

agent= _builder.compile()


#run agent

def extract_job_titles_from_resume(pdf_bytes: bytes, max_titles: int = 10) -> List[str]:
    """Parse the resume and return the job titles found in it."""
    resume_text = extract_text_from_pdf(pdf_bytes)
    return extract_titles_from_text(resume_text, max_titles=max_titles)


def run_resume_agent(
    pdf_bytes: bytes,
    job_decription: Optional[str] = None,
    job_query: Optional[str] = None,
    job_location: Optional[str] = None,
) -> dict:
  return agent.invoke({
      "pdf_bytes": pdf_bytes,
      "job_description": job_decription,
      "job_query": job_query,
      "job_location": job_location,
  })
