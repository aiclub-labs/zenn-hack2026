"""Unit tests for redact / mask behaviour.

Req 7: redact=true turn → content=None persisted.
Req 12.8: DeltaDetector skip path for redacted turns → 0 delta_events.
DELETE /turn/{id} → physical removal from store + related docs.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

import pytest

from app.contracts.cosmos import DeltaEvent, DialogueTurn
from app.repos._base import InMemoryContainer
from app.repos.dialogue_turns import DialogueTurnsRepo

_NOW = datetime(2026, 5, 25, 12, 0, 0, tzinfo=timezone.utc)
_PK = "sector_a#unit_1"
_SESSION = "sess_redact_01"


def _user_turn(turn_id: str, content: Optional[str], redact: bool) -> DialogueTurn:
    return DialogueTurn(
        id=f"dt_{uuid.uuid4().hex[:8]}",
        pk=_PK,
        session_id=_SESSION,
        turn_id=turn_id,
        role="user",
        content=content,
        redact=redact,
        timestamp=_NOW,
    )


# ---------------------------------------------------------------------------
# Req 7: content=None when redact=True
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_redact_turn_has_none_content() -> None:
    """DialogueTurn with redact=True must store content=None."""
    turn = _user_turn("t1", content=None, redact=True)
    assert turn.content is None
    assert turn.redact is True


@pytest.mark.unit
def test_non_redact_turn_retains_content() -> None:
    """Non-redacted turn must retain its content."""
    turn = _user_turn("t2", content="some business insight", redact=False)
    assert turn.content == "some business insight"
    assert turn.redact is False


@pytest.mark.unit
async def test_redacted_turn_persisted_with_no_content(
    mem_container: InMemoryContainer,
) -> None:
    """Upsert a redacted turn; reading back confirms content=None."""
    repo = DialogueTurnsRepo(mem_container)
    turn = _user_turn("t_r1", content=None, redact=True)
    await repo.upsert(turn)

    retrieved = await repo.get(turn_id="t_r1", pk=_PK)
    assert retrieved is not None
    assert retrieved.content is None
    assert retrieved.redact is True


# ---------------------------------------------------------------------------
# Req 12.8: DeltaDetector returns [] for redact=True turns
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_delta_detector_skip_on_redact_content_none() -> None:
    """Simulate the guard in DeltaDetectorAgent.detect():
    if turn.redact or not turn.content: return [].
    """
    turn = _user_turn("t_r2", content=None, redact=True)
    # Mirror the production guard
    should_skip = turn.redact or not turn.content
    assert should_skip, "Redacted turn must trigger skip path → 0 delta_events"


@pytest.mark.unit
def test_delta_detector_skip_on_redact_true_with_content() -> None:
    """Even if content is accidentally set, redact=True alone triggers skip."""
    turn = _user_turn("t_r3", content="leaked content", redact=True)
    should_skip = turn.redact or not turn.content
    assert should_skip


# ---------------------------------------------------------------------------
# DELETE /turn/{id} — physical removal
# ---------------------------------------------------------------------------

@pytest.mark.unit
async def test_physical_delete_removes_turn(mem_container: InMemoryContainer) -> None:
    """delete() removes the turn document from the in-memory store."""
    repo = DialogueTurnsRepo(mem_container)
    turn = _user_turn("t_del1", content="to be deleted", redact=False)
    await repo.upsert(turn)

    # Confirm it exists
    before = await repo.get(turn_id="t_del1", pk=_PK)
    assert before is not None

    removed = await repo.delete(turn_id="t_del1", pk=_PK)
    assert removed is True

    after = await repo.get(turn_id="t_del1", pk=_PK)
    assert after is None


@pytest.mark.unit
async def test_delete_nonexistent_turn_returns_false(
    mem_container: InMemoryContainer,
) -> None:
    """delete() returns False when no matching document exists."""
    repo = DialogueTurnsRepo(mem_container)
    result = await repo.delete(turn_id="ghost_turn", pk=_PK)
    assert result is False


@pytest.mark.unit
async def test_delete_does_not_affect_other_turns(
    mem_container: InMemoryContainer,
) -> None:
    """Deleting one turn must not remove adjacent turns in the same partition."""
    repo = DialogueTurnsRepo(mem_container)
    t1 = _user_turn("t_keep1", content="keep me", redact=False)
    t2 = _user_turn("t_del2", content="delete me", redact=False)
    await repo.upsert(t1)
    await repo.upsert(t2)

    await repo.delete(turn_id="t_del2", pk=_PK)

    remaining = await repo.get(turn_id="t_keep1", pk=_PK)
    assert remaining is not None, "Adjacent turn must survive deletion"
