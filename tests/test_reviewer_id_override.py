"""Issue #35: X-Reviewer-Id header lets UI switch reviewer profile in dev.

The override is gated on settings.environment ∈ {dev, local, development};
in prod the header must be silently ignored so Easy Auth stays authoritative.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.util import auth as auth_mod


def _req(headers: dict[str, str]) -> MagicMock:
    req = MagicMock()
    req.headers = headers
    return req


@pytest.mark.unit
def test_x_reviewer_id_honored_in_dev(monkeypatch) -> None:
    monkeypatch.setattr(auth_mod.settings, "environment", "dev")
    req = _req({"X-Reviewer-Id": "takeshi@example.com"})
    reviewer_id, scope = auth_mod.parse_easy_auth_headers(req)
    assert reviewer_id == "takeshi@example.com"
    assert scope == []


@pytest.mark.unit
def test_x_reviewer_id_ignored_in_prod(monkeypatch) -> None:
    """Prod must ignore the override so the header cannot spoof reviewers."""
    monkeypatch.setattr(auth_mod.settings, "environment", "prod")
    req = _req({"X-Reviewer-Id": "attacker@example.com"})
    reviewer_id, _ = auth_mod.parse_easy_auth_headers(req)
    assert reviewer_id == "anonymous"


@pytest.mark.unit
def test_dev_fallback_unchanged_when_override_missing(monkeypatch) -> None:
    monkeypatch.setattr(auth_mod.settings, "environment", "dev")
    req = _req({})
    reviewer_id, scope = auth_mod.parse_easy_auth_headers(req)
    assert reviewer_id == "local-dev-reviewer"
    assert scope == []
