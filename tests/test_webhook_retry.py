"""Unit tests for NotificationDispatcher webhook retry logic.

Design §6 Error / design §8 Unit:
  - 4xx → 3 retries with exponential backoff → RetryError on final failure.
  - 5xx → same 3-retry path.
  - Final failure → ErrorLog written + admin webhook fallback called.

Uses httpx.MockTransport to simulate server responses without real I/O.
KeyVaultClient is replaced with a simple stub that returns a pre-set URL.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.agents.notification.dispatcher import NotificationDispatcher
from app.contracts.events import PendingReviewEvent

_NOW = datetime(2026, 5, 25, 12, 0, 0, tzinfo=timezone.utc)
_WEBHOOK_URL = "https://discord.example.com/api/webhooks/test/token"
_ADMIN_URL = "https://discord.example.com/api/webhooks/admin/token"


def _make_event() -> PendingReviewEvent:
    return PendingReviewEvent(
        ticket_id="ft_abc123",
        sector="sector_a",
        unit="unit_1",
        user_id="user_001",
        weight_final=0.4,
        reason="final weight 0.40 < 0.5",
    )


class _FakeKV:
    """Stub KeyVaultClient — no network, returns hard-coded URLs by secret name."""

    async def get_secret(self, name: str) -> str:
        if "COST_ALERT" in name:
            return _ADMIN_URL
        return _WEBHOOK_URL


def _build_dispatcher(
    transport: httpx.MockTransport,
    error_logs_repo: Any = None,
) -> NotificationDispatcher:
    client = httpx.AsyncClient(transport=transport)
    return NotificationDispatcher(
        kv=_FakeKV(),  # type: ignore[arg-type]
        http_client=client,
        error_logs_repo=error_logs_repo,
        admin_pk="ops#default",
    )


# ---------------------------------------------------------------------------
# 4xx → 3 retries then failure
# ---------------------------------------------------------------------------

@pytest.mark.unit
async def test_4xx_triggers_three_retries_then_fails() -> None:
    """Discord 4xx → dispatcher retries 3 times total then falls through to failure path."""
    call_count = 0

    def _handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(400, json={"message": "Bad Request"})

    error_logs_repo = AsyncMock()
    error_logs_repo.append = AsyncMock()

    transport = httpx.MockTransport(_handler)
    dispatcher = _build_dispatcher(transport, error_logs_repo=error_logs_repo)

    await dispatcher.emit(_make_event())

    # tenacity stop_after_attempt(3): 3 attempts made to the webhook URL
    # + 1 attempt to admin fallback on the failure path
    assert call_count >= 3, f"Expected ≥3 webhook calls; got {call_count}"


@pytest.mark.unit
async def test_5xx_triggers_three_retries_then_fails() -> None:
    """Discord 5xx → same 3-retry path."""
    call_count = 0

    def _handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(500, json={"message": "Internal Server Error"})

    error_logs_repo = AsyncMock()
    transport = httpx.MockTransport(_handler)
    dispatcher = _build_dispatcher(transport, error_logs_repo=error_logs_repo)

    await dispatcher.emit(_make_event())

    assert call_count >= 3, f"Expected ≥3 webhook calls; got {call_count}"


# ---------------------------------------------------------------------------
# Final failure → error_logs written + admin fallback
# ---------------------------------------------------------------------------

@pytest.mark.unit
async def test_final_failure_writes_error_log_and_admin_fallback() -> None:
    """After all retries exhausted, error_logs.append() is called and admin URL hit."""
    admin_calls: list[str] = []
    primary_calls = 0

    def _handler(request: httpx.Request) -> httpx.Response:
        nonlocal primary_calls
        url = str(request.url)
        if "admin" in url:
            admin_calls.append(url)
            return httpx.Response(204)  # admin succeeds
        primary_calls += 1
        return httpx.Response(400, json={"message": "Bad Request"})

    error_logs_repo = AsyncMock()
    error_logs_repo.append = AsyncMock()

    transport = httpx.MockTransport(_handler)
    dispatcher = _build_dispatcher(transport, error_logs_repo=error_logs_repo)

    await dispatcher.emit(_make_event())

    # ErrorLog must have been persisted
    error_logs_repo.append.assert_called_once()
    # Admin fallback webhook must have been called
    assert len(admin_calls) >= 1, "Admin fallback webhook must be called on failure"


@pytest.mark.unit
async def test_success_on_first_attempt_no_error_log() -> None:
    """When Discord responds 204 on the first attempt, no error_log is written."""

    def _handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(204)

    error_logs_repo = AsyncMock()
    error_logs_repo.append = AsyncMock()

    transport = httpx.MockTransport(_handler)
    dispatcher = _build_dispatcher(transport, error_logs_repo=error_logs_repo)

    await dispatcher.emit(_make_event())

    error_logs_repo.append.assert_not_called()


@pytest.mark.unit
async def test_success_after_transient_failure() -> None:
    """Transient failure on attempt 1-2, success on attempt 3 → no error_log."""
    attempts = 0

    def _handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        if "admin" in str(request.url):
            return httpx.Response(204)
        attempts += 1
        if attempts < 3:
            return httpx.Response(500)
        return httpx.Response(204)

    error_logs_repo = AsyncMock()
    error_logs_repo.append = AsyncMock()

    transport = httpx.MockTransport(_handler)
    dispatcher = _build_dispatcher(transport, error_logs_repo=error_logs_repo)

    await dispatcher.emit(_make_event())

    error_logs_repo.append.assert_not_called()
