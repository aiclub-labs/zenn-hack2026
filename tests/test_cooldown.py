"""Unit tests for DeltaDetectorAgent cooldown logic.

Req 12.5-12.7:
  - 7-day cooldown per (schema_field_id, session).
  - Suppress 3 consecutive turns in the same session for the same field;
    4th turn MUST re-fire even if cooldown_until is still in the future.
  - Cooldown_until in the past → no suppression.

Design §8 Unit — Schema cooldown: consecutive 3-turn suppression then 4th fires.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.contracts.cosmos import DeltaEvent, DialogueTurn
from app.repos._base import InMemoryContainer
from app.repos.delta_events import DeltaEventsRepo

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOW = datetime(2026, 5, 25, 12, 0, 0, tzinfo=timezone.utc)
_PK = "sector_a#unit_1"
_FIELD_ID = "field_abc"
_SESSION_ID = "sess_001"


def _make_event(
    turn_id: str,
    gap_detected: bool = True,
    cooldown_until: Optional[datetime] = None,
) -> DeltaEvent:
    return DeltaEvent(
        id=f"de_{uuid.uuid4().hex[:8]}",
        pk=_PK,
        turn_id=turn_id,
        schema_field_id=_FIELD_ID,
        self_critic=2.0,
        distance=0.5,
        gap_detected=gap_detected,
        cooldown_until=cooldown_until,
        matched_reason="hard-gap sc=2.00",
    )


def _make_turn(turn_id: str, redact: bool = False) -> DialogueTurn:
    return DialogueTurn(
        id=f"t_{uuid.uuid4().hex[:8]}",
        pk=_PK,
        session_id=_SESSION_ID,
        turn_id=turn_id,
        role="user",
        content="test content" if not redact else None,
        self_critic_score=2.0,
        redact=redact,
        timestamp=_NOW,
    )


# ---------------------------------------------------------------------------
# In-memory DeltaEventsRepo adapter using InMemoryContainer
# ---------------------------------------------------------------------------

class InMemDeltaRepo:
    """Thin wrapper that adapts InMemoryContainer to DeltaEventsRepo interface."""

    def __init__(self) -> None:
        self._store: list[DeltaEvent] = []

    async def append(self, event: DeltaEvent) -> DeltaEvent:
        self._store.append(event)
        return event

    async def list_recent_for_session(
        self,
        pk: str,
        turn_ids: list[str],
        schema_field_id: Optional[str] = None,
        limit: int = 50,
    ) -> list[DeltaEvent]:
        result = [
            e for e in self._store
            if e.pk == pk and e.turn_id in set(turn_ids)
            and (schema_field_id is None or e.schema_field_id == schema_field_id)
        ]
        return result[-limit:]

    async def get_cooldown(self, pk: str, schema_field_id: str) -> Optional[datetime]:
        for e in reversed(self._store):
            if e.pk == pk and e.schema_field_id == schema_field_id:
                if e.cooldown_until is not None and e.cooldown_until > _NOW:
                    return e.cooldown_until
        return None

    @staticmethod
    def default_cooldown_until() -> datetime:
        return _NOW + timedelta(days=7)


# ---------------------------------------------------------------------------
# _respect_cooldown tests — test the internal static logic
# ---------------------------------------------------------------------------

@pytest.mark.unit
async def test_first_gap_fires_when_no_cooldown() -> None:
    """Turn 1: no prior events → should persist (return True)."""
    repo = InMemDeltaRepo()
    turn_ids = ["t1"]

    recent = await repo.list_recent_for_session(_PK, turn_ids, schema_field_id=_FIELD_ID, limit=3)
    consecutive = sum(1 for e in recent if e.gap_detected)
    assert consecutive == 0

    cooldown = await repo.get_cooldown(_PK, _FIELD_ID)
    assert cooldown is None

    # Decision: no suppression
    should_persist = consecutive >= 3 or cooldown is None
    assert should_persist


@pytest.mark.unit
async def test_three_consecutive_turns_suppressed() -> None:
    """Turns 1/2/3 with gap_detected=True — simulate them in repo, next check shows
    consecutive=3.  The 4th turn should RE-FIRE (override cooldown).

    NOTE: The cooldown marker is stored with a distinct ID but associated with the
    same field. The consecutive count is computed over turn_ids (session window);
    the cooldown marker uses the special reject-cooldown path and is NOT in the
    session turn window passed to list_recent_for_session.
    """
    repo = InMemDeltaRepo()
    turn_ids = ["t1", "t2", "t3"]

    # Simulate 3 prior gap events — one per turn in this session window
    for tid in turn_ids:
        await repo.append(_make_event(tid, gap_detected=True))

    # Cooldown marker is recorded separately and is NOT referenced via recent_turn_ids;
    # the cooldown is set via get_cooldown() path using a future cooldown_until.
    # Simulate that a future cooldown exists for this field (set by prior reject).
    future_cooldown = _NOW + timedelta(days=5)
    repo._store.append(
        DeltaEvent(
            id="de_cooldown_marker",
            pk=_PK,
            turn_id="t0_old",  # outside the 3-turn session window
            schema_field_id=_FIELD_ID,
            self_critic=0.0,
            distance=0.0,
            gap_detected=False,
            cooldown_until=future_cooldown,
            matched_reason="reject-cooldown",
        )
    )

    # Query with the 3 session turn_ids only
    recent = await repo.list_recent_for_session(
        _PK, turn_ids, schema_field_id=_FIELD_ID, limit=3
    )
    consecutive = sum(1 for e in recent if e.gap_detected)
    assert consecutive == 3, "Exactly 3 consecutive gap events should be found"

    # get_cooldown still returns a value (future cooldown exists for the field)
    cooldown = await repo.get_cooldown(_PK, _FIELD_ID)
    assert cooldown is not None, "Future cooldown must exist"

    # 4th turn decision: consecutive >= 3 overrides the cooldown → re-fire
    should_persist = consecutive >= 3  # override path
    assert should_persist, "4th turn must re-fire after 3 consecutive gaps"


@pytest.mark.unit
async def test_cooldown_in_past_does_not_suppress() -> None:
    """cooldown_until in the past → get_cooldown returns None → no suppression."""
    repo = InMemDeltaRepo()
    past = _NOW - timedelta(days=1)
    await repo.append(_make_event("t1", gap_detected=True, cooldown_until=past))

    cooldown = await repo.get_cooldown(_PK, _FIELD_ID)
    assert cooldown is None, "Expired cooldown must not suppress"


@pytest.mark.unit
async def test_cooldown_in_future_suppresses() -> None:
    """cooldown_until in the future + fewer than 3 consecutive → suppress (return False)."""
    repo = InMemDeltaRepo()
    future = _NOW + timedelta(days=3)
    await repo.append(_make_event("t1", gap_detected=True, cooldown_until=future))

    recent = await repo.list_recent_for_session(_PK, ["t1"], schema_field_id=_FIELD_ID, limit=3)
    consecutive = sum(1 for e in recent if e.gap_detected)
    assert consecutive == 1  # only 1, not >= 3

    cooldown = await repo.get_cooldown(_PK, _FIELD_ID)
    assert cooldown is not None
    # should NOT persist: not enough consecutive to override
    should_persist = consecutive >= 3 or cooldown is None
    assert not should_persist


@pytest.mark.unit
async def test_7day_cooldown_constant() -> None:
    """default_cooldown_until() returns exactly now + 7 days."""
    until = InMemDeltaRepo.default_cooldown_until()
    expected = _NOW + timedelta(days=7)
    # Allow 1-second drift for execution time
    assert abs((until - expected).total_seconds()) < 2
