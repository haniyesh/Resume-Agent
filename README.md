ResumeAI: Resume Parser and Reviewer

ResumeAI tailors an existing resume to a job description using a local LLM
(Ollama). Factual fields are extracted deterministically by a parser, so the
model can never invent skills, drop projects, or fabricate contact details. The
LLM is used only to write the summary, and that summary is rejected if it
mentions anything absent from the source resume.

## Installation

```
pip install -r requirements.txt
ollama serve
ollama pull llama3.2:3b
```

## Usage

The pipeline reads a resume, reads a job description, and writes a tailored PDF.

```
python src/agent/agent_pipeline.py
```

Inputs (override with env vars, see `.env.example`):

- `RESUME_PATH` — path to a `.txt` or `.pdf` resume (default `src/data/resume.txt`)
- `LLM_MODEL` — Ollama model tag (default `llama3.2:3b`)
- `OLLAMA_BASE_URL` — Ollama server (default `http://localhost:11434`)

The job description is read from `src/data/sample_job.txt`; the output PDF is
written to `src/data/output_resume.pdf`.

Use the exact model tag Ollama reports (`ollama list`). A bare `llama3.2` will
404 against a `llama3.2:3b` pull.

## How the anti-hallucination check works

1. `src/agent/resume_parser.py` extracts name, contact, skills, projects, and
   education with regexes. Nothing here is model-generated.
2. The LLM is asked for a summary only. If the summary names a tool that does
   not appear in the source resume, it is discarded and a plain summary is used
   instead.
3. Skills are re-ordered toward job-description keywords, but never added.

## React Dashboard

A React + FastAPI dashboard is available in `dashboard/`.

### Backend (FastAPI)

```
uvicorn dashboard.backend.main:app --reload
```

The API listens on `http://localhost:8000` and exposes:

- `POST /api/extract-titles` — upload a resume PDF, returns extracted job titles.
- `POST /api/search-jobs` — search Adzuna for a title + optional location.
- `GET /api/health` — health check.

### Frontend (React + Vite)

```
cd dashboard/frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Project Structure

- `src/agent/agent_pipeline.py` — end-to-end pipeline.
- `src/agent/resume_parser.py` — deterministic fact extraction.
- `src/agent/tailoring/pdf_parser.py` — PDF text extraction.
- `src/agent/tailoring/pdf_generator.py` — PDF rendering.
- `src/config/prompts.py` — LLM prompts.
- `dashboard/backend/` — FastAPI app.
- `dashboard/frontend/` — React + Vite UI.
- `tests/` — Pytest tests.
