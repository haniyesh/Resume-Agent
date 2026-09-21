import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest

from src.utils import search_jobs as search_jobs_module


SAMPLE_RESULT = {
    "id": 12345,
    "title": "Data Engineer",
    "company": {"display_name": "Acme Corp"},
    "location": {"area": ["Remote", "London", "UK"], "display_name": "Remote, London, UK"},
    "salary_min": 50000,
    "salary_max": 70000,
    "currency": "GBP",
    "salary_is_estimated": False,
    "description": "<p>Build pipelines</p>",
    "redirect_url": "https://www.adzuna.co.uk/jobs/details/12345",
    "category": {"label": "IT Jobs"},
    "created": "2026-09-20T10:00:00Z",
}

LOCAL_RESULT = {
    "id": 1,
    "title": "Data Engineer",
    "company": {"display_name": "Acme Corp"},
    "location": {"area": ["London", "UK"], "display_name": "London, UK"},
    "redirect_url": "https://example.com/1",
}

OTHER_RESULT = {
    "id": 2,
    "title": "Data Engineer",
    "company": {"display_name": "Other Corp"},
    "location": {"area": ["Manchester", "UK"], "display_name": "Manchester, UK"},
    "redirect_url": "https://example.com/2",
}

REMOTE_RESULT = {
    "id": 3,
    "title": "Data Engineer",
    "company": {"display_name": "Remote Corp"},
    "location": {"area": ["Berlin", "Germany"], "display_name": "Remote, Berlin, Germany"},
    "redirect_url": "https://example.com/3",
}


def _fake_response(payload):
    return type(
        "FakeResponse",
        (),
        {
            "status_code": 200,
            "raise_for_status": lambda self: None,
            "json": lambda self: payload,
        },
    )()


@pytest.fixture
def creds(monkeypatch):
    monkeypatch.setattr(search_jobs_module, "ADZUNA_APP_ID", "test-id")
    monkeypatch.setattr(search_jobs_module, "ADZUNA_APP_KEY", "test-key")


def test_search_jobs_requires_credentials(monkeypatch):
    monkeypatch.setattr(search_jobs_module, "ADZUNA_APP_ID", None)
    monkeypatch.setattr(search_jobs_module, "ADZUNA_APP_KEY", None)

    with pytest.raises(ValueError, match="ADZUNA_APP_ID"):
        search_jobs_module.search_jobs("data engineer", location="London")


def test_search_jobs_normalizes_results(creds, monkeypatch):
    monkeypatch.setattr(
        search_jobs_module.requests,
        "get",
        lambda url, params=None, headers=None, timeout=30: type(
            "FakeResponse",
            (),
            {
                "status_code": 200,
                "raise_for_status": lambda self: None,
                "json": lambda self: {"count": 3, "page": 1, "results": [SAMPLE_RESULT]},
            },
        )(),
    )

    result = search_jobs_module.search_jobs("data engineer", location="London")

    assert result["count"] == 1
    job = result["results"][0]
    assert job["title"] == "Data Engineer"
    assert job["company"] == "Acme Corp"
    assert job["location"] == "Remote, London, UK"
    assert job["locations"] == ["Remote", "London", "UK"]
    assert job["salary_min"] == 50000
    assert job["url"] == "https://www.adzuna.co.uk/jobs/details/12345"
    assert job["remote"] is True


def test_search_jobs_empty_results(creds, monkeypatch):
    monkeypatch.setattr(
        search_jobs_module.requests,
        "get",
        lambda url, params=None, headers=None, timeout=30: type(
            "FakeResponse",
            (),
            {
                "status_code": 200,
                "raise_for_status": lambda self: None,
                "json": lambda self: {"count": 0, "page": 1, "results": []},
            },
        )(),
    )

    result = search_jobs_module.search_jobs("nonexistent-role")

    assert result["results"] == []
    assert result["count"] == 0


def test_filters_out_jobs_outside_region(creds, monkeypatch):
    payload = {"count": 2, "page": 1, "results": [LOCAL_RESULT, OTHER_RESULT]}
    monkeypatch.setattr(
        search_jobs_module.requests,
        "get",
        lambda url, params=None, headers=None, timeout=30: _fake_response(payload),
    )

    result = search_jobs_module.search_jobs("data engineer", location="London")

    assert [job["id"] for job in result["results"]] == ["1"]
    assert result["count"] == 1


def test_region_filter_keeps_remote_jobs(creds, monkeypatch):
    monkeypatch.setattr(
        search_jobs_module.requests,
        "get",
        lambda url, params=None, headers=None, timeout=30: _fake_response(
            {"count": 2, "page": 1, "results": [LOCAL_RESULT, REMOTE_RESULT]}
        ),
    )

    result = search_jobs_module.search_jobs("data engineer", location="London")

    assert {job["id"] for job in result["results"]} == {"1", "3"}
    remote = next(job for job in result["results"] if job["id"] == "3")
    assert remote["remote"] is True