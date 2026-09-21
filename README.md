
# ResumeAI: Resume Parser and Reviewer

ResumeAI is an advanced tool that leverages the power of Large Language Models (LLMs) to analyze and improve resumes. This Streamlit-based application allows users to upload their resumes, optionally provide a job description, and receive detailed analysis and improvement suggestions.

## Features

- **Resume Parsing**: Extracts text from PDF resumes and parses it into a structured format.
- **Resume Review**: Analyzes the parsed resume, considering an optional job description.
- **Section-by-Section Analysis**: Provides a detailed review of each section of the resume.
- **Improvement Suggestions**: Offers revision suggestions with impact levels for each section.
- **Interactive UI**: User-friendly interface with section navigation and side-by-side comparison of original and revised content.

## Installation

1. Clone the repository:

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Make sure Ollama is installed and running (`ollama serve`), then pull a model:
   ```
   ollama pull llama3.2
   ```

2. Run the Streamlit app:
   ```
   PYTHONPATH=$(pwd) streamlit run src/app.py --server.enableXsrfProtection false
   ```

3. Open your web browser and navigate to the provided local URL (usually `http://localhost:8501`).

4. Upload your resume PDF file using the file uploader in the sidebar.

5. (Optional) Enter a job description in the text area provided.

6. Click the "Run Analysis" button to start the resume parsing and review process.

7. Navigate through different sections of your resume using the arrow buttons.

8. Review the original content, revised content, and improvement suggestions for each section.

## Configuration

LLM settings are read from `.env` (see `.env.example`):

- `OLLAMA_BASE_URL`: Ollama server URL (default `http://localhost:11434`).
- `LLM_MODEL`: Ollama model to use (default `llama3.2`).

## React Dashboard

A React + FastAPI dashboard is available in `dashboard/`. It reuses the same
Python logic in `src/` (resume parsing, LLM job-title extraction, Adzuna search).

### Backend (FastAPI)

From the project root:

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

Open `http://localhost:5173`. The frontend talks to the backend at
`http://localhost:8000` by default; override with a `VITE_API_BASE` env var.

## Project Structure

- `src/`: Shared Python logic (PDF parsing, LLM prompts, Adzuna search).
- `src/utils/pdf.py`: Functions for extracting text from PDF files.
- `src/utils/llm.py`: Parsing resumes, extracting job titles, and reviewing via LLMs.
- `src/utils/search_jobs.py`: Adzuna job search client.
- `dashboard/backend/`: FastAPI app exposing the Python logic as a REST API.
- `dashboard/frontend/`: React + Vite dashboard UI.
- `tests/`: Pytest tests.
- `src/app.py`: Legacy Streamlit application.

## Dependencies

- Streamlit
- PyYAML
- (Other dependencies as listed in `requirements.txt`)
