import requests


REMOTIVE_API_URL = "https://remotive.com/api/remote-jobs"


def _normalize_job(job):
    location = job.get("candidate_required_location") or ""
    return {
        "id": f"remotive-{job.get('id')}",
        "title": job.get("title"),
        "company": job.get("company_name"),
        "locations": [location] if location else [],
        "location": location,
        "salary_min": None,
        "salary_max": None,
        "currency": None,
        "salary_is_estimated": False,
        "salary_text": job.get("salary") or None,
        "description": job.get("description"),
        "url": job.get("url"),
        "category": job.get("category"),
        "posted": job.get("publication_date"),
        "job_type": job.get("job_type"),
        "remote": True,
        "source": "remotive",
    }


def search_remote_jobs(query, limit=None, timeout=30):
    """Search remote job listings on Remotive (all listings are remote)."""
    params = {"search": query}
    if limit:
        params["limit"] = limit

    response = requests.get(REMOTIVE_API_URL, params=params, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    return [_normalize_job(job) for job in payload.get("jobs", [])]
