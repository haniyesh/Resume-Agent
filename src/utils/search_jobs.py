import time

import requests
from config import ADZUNA_APP_ID, ADZUNA_APP_KEY, ADZUNA_COUNTRY, ADZUNA_RESULTS_PER_PAGE


API_URL = "https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"

RETRYABLE_STATUS = {502, 503, 429}

REMOTE_TERMS = ("remote", "work from home", "work-from-home", "wfh", "telecommute")


def _request_with_retry(url, params, headers, timeout, max_retries=3):
    """GET with retries and exponential backoff on transient failures.

    Retries only when Adzuna is briefly unavailable (502/503/429) or the
    connection drops. Permanent errors (e.g. 400) are returned immediately.
    """
    last_exc = None
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=timeout)
        except requests.RequestException as exc:
            last_exc = exc
        else:
            if response.status_code not in RETRYABLE_STATUS:
                return response
            last_exc = None
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)
    if last_exc is not None:
        raise last_exc
    return response


def _is_remote(job):
    location = job.get("location") or {}
    text = " ".join(
        [
            str(job.get("title") or ""),
            str(location.get("display_name") or ""),
            " ".join(str(area) for area in location.get("area") or []),
        ]
    ).lower()
    return any(term in text for term in REMOTE_TERMS)


def _normalize_job(job):
    return {
        "id": str(job.get("id")),
        "title": job.get("title"),
        "company": (job.get("company") or {}).get("display_name"),
        "locations": (job.get("location") or {}).get("area") or [],
        "location": (job.get("location") or {}).get("display_name"),
        "salary_min": job.get("salary_min"),
        "salary_max": job.get("salary_max"),
        "currency": job.get("currency"),
        "salary_is_estimated": job.get("salary_is_estimated", False),
        "description": job.get("description"),
        "url": job.get("redirect_url"),
        "category": (job.get("category") or {}).get("label"),
        "posted": job.get("created"),
        "remote": _is_remote(job),
    }


def _matches_region(job, region):
    region = (region or "").strip().lower()
    if not region:
        return True
    display = str(job.get("location") or "").lower()
    areas = " ".join(str(area) for area in job.get("locations") or []).lower()
    return region in display or region in areas


def _fetch_jobs(
    query,
    location,
    *,
    country,
    results_per_page,
    category,
    salary_min,
    max_days_old,
    timeout,
):
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": results_per_page or ADZUNA_RESULTS_PER_PAGE,
        "what": query,
        "max_days_old": max_days_old,
    }
    if location:
        params["where"] = location
    if category:
        params["category"] = category
    if salary_min:
        params["salary_min"] = salary_min

    url = API_URL.format(country=country or ADZUNA_COUNTRY, page=1)
    response = _request_with_retry(
        url, params=params, headers={"Content-Type": "application/json"}, timeout=timeout
    )
    response.raise_for_status()
    payload = response.json()

    jobs = [_normalize_job(job) for job in payload.get("results", [])]
    return jobs


def search_jobs(
    query,
    location=None,
    country=None,
    results_per_page=None,
    category=None,
    salary_min=None,
    max_days_old=None,
    timeout=30,
):
    """Search live job listings on Adzuna and return normalized results.

    When ``location`` is given, only jobs based in that region are kept, plus
    remote roles (which can be done from anywhere).
    """
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        raise ValueError(
            "Adzuna credentials are missing. Set ADZUNA_APP_ID and ADZUNA_APP_KEY in your .env file."
        )

    fetch_options = {
        "country": country,
        "results_per_page": results_per_page,
        "category": category,
        "salary_min": salary_min,
        "max_days_old": max_days_old,
        "timeout": timeout,
    }

    jobs = _fetch_jobs(query, location, **fetch_options)
    if location:
        jobs = [job for job in jobs if job["remote"] or _matches_region(job, location)]

    return {
        "count": len(jobs),
        "page": 1,
        "results": jobs,
    }
