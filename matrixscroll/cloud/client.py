"""Low-level HTTP client for ssx360.com platform APIs."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

DEFAULT_BASE_URL = "https://ssx360.com"
SIGNUP_URL = "https://ssx360.com/signup"
DOCS_URL = "https://ssx360.com/docs"


class CloudAuthError(Exception):
    """Raised when SSX360_API_KEY is missing or rejected."""

    def __init__(self, payload: dict[str, Any]) -> None:
        super().__init__(payload.get("message") or payload.get("error") or "API key required")
        self.payload = payload


def _require_api_key() -> str:
    key = os.environ.get("SSX360_API_KEY", "").strip()
    if key:
        return key
    raise CloudAuthError(
        {
            "ok": False,
            "error": "api_key_required",
            "message": (
                "Network features require SSX360_API_KEY. "
                "Community tier includes 100 CI verifications/day. "
                f"Get a key at {SIGNUP_URL}"
            ),
            "signup_url": SIGNUP_URL,
            "docs_url": DOCS_URL,
        }
    )


def _request(method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    api_key = _require_api_key()
    base = os.environ.get("SSX360_API_BASE", DEFAULT_BASE_URL).rstrip("/")
    url = f"{base}{path}"
    data = None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"ok": False, "error": "http_error", "message": raw or str(exc)}
        if exc.code in (401, 403, 429):
            raise CloudAuthError(payload) from exc
        raise RuntimeError(payload.get("message") or payload.get("error") or raw) from exc


def verify_range(
    *,
    base: str = "origin/main",
    head: str = "HEAD",
    commits: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Hosted Scroll Gate verification via ssx360.com/api/v1/verify."""
    return _request(
        "POST",
        "/api/v1/verify",
        {"base": base, "head": head, "commits": commits or []},
    )


def list_envelopes(*, limit: int = 50) -> dict[str, Any]:
    """List stored envelopes for the authenticated organization."""
    return _request("GET", f"/api/v1/envelopes?limit={limit}")


def audit_export(*, format: str = "json") -> dict[str, Any]:
    """Export audit bundle from the hosted platform (Team+)."""
    return _request("GET", f"/api/v1/audit/export?format={format}")
