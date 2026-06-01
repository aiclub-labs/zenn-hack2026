"""Issue #31: GET /schemas/history/public exposes schema changelog to
業務ユーザー (no admin role) and masks ``changed_by`` to "reviewer"
so reviewer identity does not leak.

Direct-coroutine style (no TestClient) — sidesteps the httpx/starlette
version skew the other tests in this repo work around the same way.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from app.api import schemas as schemas_api
from app.contracts.common import Tenant
from app.contracts.cosmos import SchemaAuditEntry


def _entry(field_id: str, changed_by: str) -> SchemaAuditEntry:
    return SchemaAuditEntry(
        id=f"audit-{field_id}",
        pk="manufacturing-s8b#line-A",
        schema_field_id=field_id,
        revision_id=2,
        change_type="update",
        diff={"description": {"before": "old", "after": "new"}},
        reason="UAT",
        changed_by=changed_by,
        changed_at=datetime(2026, 5, 28, tzinfo=timezone.utc),
    )


def _stub_agent() -> AsyncMock:
    agent = AsyncMock()
    agent.get_history = AsyncMock(
        return_value=[
            _entry("sf_a", "takeshi@example.com"),
            _entry("sf_b", "haruka@example.com"),
        ]
    )
    return agent


@pytest.mark.unit
def test_public_history_no_admin_dep_in_signature() -> None:
    """The public endpoint must NOT depend on ``require_admin_role`` —
    that's the whole point of Issue #31."""
    import inspect

    sig = inspect.signature(schemas_api.get_history_public)
    deps = [p for p in sig.parameters.values() if p.default is not inspect.Parameter.empty]
    # ``require_admin_role`` is a fastapi.Depends; assert no parameter
    # carries it as its default callable.
    for p in deps:
        d = p.default
        cb = getattr(d, "dependency", None)
        assert cb is not schemas_api.require_admin_role, (
            f"parameter {p.name!r} must not depend on require_admin_role"
        )


@pytest.mark.unit
def test_public_history_returns_rows_and_calls_agent() -> None:
    agent = _stub_agent()
    rows = asyncio.run(
        schemas_api.get_history_public(
            sector="manufacturing-s8b",
            unit="line-A",
            limit=50,
            since=None,
            agent=agent,
        )
    )
    assert len(rows) == 2
    agent.get_history.assert_awaited_once()
    call_kwargs = agent.get_history.await_args.kwargs
    assert call_kwargs["tenant"] == Tenant(sector="manufacturing-s8b", unit="line-A")


@pytest.mark.unit
def test_public_history_masks_changed_by() -> None:
    """``changed_by`` must be ``"reviewer"`` for every row (PII guard)."""
    agent = _stub_agent()
    rows = asyncio.run(
        schemas_api.get_history_public(
            sector="manufacturing-s8b",
            unit="line-A",
            limit=50,
            since=None,
            agent=agent,
        )
    )
    for row in rows:
        assert row.changed_by == "reviewer"


@pytest.mark.unit
def test_admin_history_still_admin_gated() -> None:
    """Regression guard: original ``/history`` route still has the
    admin-role dependency."""
    import inspect

    sig = inspect.signature(schemas_api.get_history)
    found_admin_dep = False
    for p in sig.parameters.values():
        d = p.default
        if d is inspect.Parameter.empty:
            continue
        cb = getattr(d, "dependency", None)
        if cb is schemas_api.require_admin_role:
            found_admin_dep = True
            break
    assert found_admin_dep, "/history must keep require_admin_role"
