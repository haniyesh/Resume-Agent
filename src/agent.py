from io import BytesIO
from typing import Optional, TypeDict, List
import yaml
from utils.pdf import extract_text_from_pdf
from utils.llm import pars_resume, review_resume
from utils.resume_pdf import  generate_resume_pdf, parse_resume, review_resume, generate_cover_letter
from langgraph.graph import StateGraph, START, END
from utils.resume_pdf import merge_revised_resume, generate_resume_pdf

#inpute:resume_pdf:bytes
class AgentState(TypeDict):
  pdf_bytes: bytes
  resume_text: str #stage_1 output
  resume_yaml: str #stage_2 output
  resume_data: dict               # stage 2 parsed (dict)
  job_description: Optional[str]
  review_data: dict               # stage 3 output
  revised_resume: dict            # stage 4 input
  pdf_output: bytes               # stage 4 output

  errors: List[str]
# define nodes  
def extract_text(state: AgentState) -> dict:
  return { "resume_text": extract_text_from_pdf(state["pdf_bytes"]) }

#input:resume_text, output:resume_yaml
def parse(state: AgentState) -> dict:
  resume_yaml =pars_resume(state["resume_text"])
  return { "resume_yaml": resume_yaml, "resume_data": yaml.safe_load(resume_yaml)  }


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
_builder.add_node("review_resume", review)
_builder.add_node("merge_and_build_pdf", merge_and_build_pdf)


_builder.add_edge(START, "extract_text")
_builder.add_edge("extract_text", "parse")
_builder.add_edge("parse", "review_resume")
_builder.add_edge("review_resume", "merge_and_build_pdf")
_builder.add_edge("merge_and_build_pdf", END)

agent= _builder.build()


#run agent

def run_resume_agent(pdf_bytes: bytes, job_decription:Optional[str] =None) -> dict:
  return agent.invoke({"pdf_bytes": pdf_bytes, "job_description": job_decription})