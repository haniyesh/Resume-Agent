import sys
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from agent import extract_job_titles_from_resume  # noqa: E402
from utils.remotive import search_remote_jobs  # noqa: E402
from utils.search_jobs import search_jobs  # noqa: E402


app = FastAPI(title="Resume Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/extract-titles")
async def extract_titles(pdf: UploadFile = File(...)):
    """Extract job titles from an uploaded resume PDF."""
    contents = await pdf.read()
    try:
        titles = extract_job_titles_from_resume(contents)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Resume parsing failed: {exc}") from exc
    return {"titles": titles}


class SearchRequest(BaseModel):
    query: str
    location: Optional[str] = None
    results_per_page: Optional[int] = None


@app.post("/api/search-jobs")
def search(search: SearchRequest):
    """Search live on-site listings on Adzuna, plus remote roles from Remotive."""
    try:
        result = search_jobs(
            search.query,
            location=search.location,
            results_per_page=search.results_per_page,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Adzuna search failed: {exc}") from exc

    jobs = result["results"]
    if search.location:
        try:
            remote_jobs = search_remote_jobs(search.query)
        except Exception:  # noqa: BLE001
            remote_jobs = []
        seen = {job["id"] for job in jobs}
        for job in remote_jobs:
            if job["id"] not in seen:
                jobs.append(job)
                seen.add(job["id"])

    return {
        "count": len(jobs),
        "jobs": jobs,
    }