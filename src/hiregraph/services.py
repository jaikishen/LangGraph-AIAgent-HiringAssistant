from __future__ import annotations
import time
import uuid
from hiregraph.config import get_settings


class EmailSendError(Exception):
    """Raised when the email service fails. Triggers RetryPolicy."""


class ATSUpdateError(Exception):
    """Raised when the ATS update fails. Triggers RetryPolicy."""


# ---------------------------------------------------------------------------
# Web search (Tavily)
# ---------------------------------------------------------------------------

def _mock_tavily_search(query: str) -> list[dict]:
    q = query.lower()
    if "pycon" in q or "talk" in q:
        return [{"title": "Mock: PyCon talk found", "url": "https://example.com", "content": "Speaker on async Python."}]
    if "github" in q or "open source" in q:
        return [{"title": "Mock: GitHub activity found", "url": "https://github.com/mock", "content": "Active contributor."}]
    return [{"title": "Mock: search result", "url": "https://example.com", "content": "General result."}]


def _real_tavily_search(query: str) -> list[dict]:
    from tavily import TavilyClient
    client = TavilyClient(api_key=get_settings().tavily_api_key)
    response = client.search(query=query, max_results=3)
    return response.get("results", [])


def tavily_search(query: str) -> list[dict]:
    if get_settings().use_mocks:
        return _mock_tavily_search(query)
    return _real_tavily_search(query)


# ---------------------------------------------------------------------------
# GitHub profile
# ---------------------------------------------------------------------------

def _mock_github_profile(username: str) -> dict:
    profiles = {
        "priyaram-eng": {"repos": 34, "stars": 210, "languages": ["Python", "Go"], "bio": "Backend engineer"},
        "eitanschreiber": {"repos": 12, "stars": 45, "languages": ["Python", "JavaScript"], "bio": "Full-stack dev"},
        "mira-dev": {"repos": 8, "stars": 20, "languages": ["JavaScript", "TypeScript", "CSS"], "bio": "Frontend"},
    }
    return profiles.get(username, {"repos": 5, "stars": 10, "languages": ["Python"], "bio": "Developer"})


def _real_github_profile(username: str) -> dict:
    import httpx
    headers = {"Accept": "application/vnd.github+json"}
    token = get_settings().github_token
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = httpx.get(f"https://api.github.com/users/{username}", headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return {
        "repos": data.get("public_repos", 0),
        "stars": 0,
        "languages": [],
        "bio": data.get("bio") or "",
    }


def github_profile(username: str) -> dict:
    if get_settings().use_mocks:
        return _mock_github_profile(username)
    return _real_github_profile(username)


# ---------------------------------------------------------------------------
# Email send (mock only — real via Mailtrap in bonus phase)
# ---------------------------------------------------------------------------

def _mock_send_email(to: str, subject: str, body: str) -> None:
    time.sleep(0.01)
    print(f"[mock-email] to={to!r} subject={subject!r}\n{body[:120]}...\n")


def send_email(to: str, subject: str, body: str) -> None:
    if get_settings().use_mocks:
        return _mock_send_email(to, subject, body)
    raise NotImplementedError("Real email send not configured — set HIREGRAPH_USE_MOCKS=true or configure Mailtrap")


# ---------------------------------------------------------------------------
# ATS update (mock only)
# ---------------------------------------------------------------------------

def _mock_update_ats(candidate_id: str, recommendation: str) -> str:
    record_id = f"ATS-{uuid.uuid4().hex[:6].upper()}"
    print(f"[mock-ats] logged {candidate_id} → {recommendation} as {record_id}")
    return record_id


def update_ats(candidate_id: str, recommendation: str) -> str:
    if get_settings().use_mocks:
        return _mock_update_ats(candidate_id, recommendation)
    raise NotImplementedError("Real ATS not configured — set HIREGRAPH_USE_MOCKS=true")
