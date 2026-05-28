"""Unit tests for Hearout Agent ChatExtract follow-up behaviour (Req 5).

Req 5:
  - Hearout ChatExtract presents inferred 5W1H summary.
  - If user says "違う" / "no" → record discarded, slot cleared.
  - 5-turn limit: 5th turn without resolution → outcome=expired.
  - SKIP → outcome=skipped, partial record persisted.

The HearoutAgent depends on an LLM; tests replace the LLM with a stub that
returns scripted JSON responses so we exercise the state-machine without I/O.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.hearout.agent import HearoutAgent
from app.agents.hearout.state import HearoutSessionState
from app.contracts.common import Tenant
from app.contracts.cosmos import HearoutRecord
from app.repos._base import InMemoryContainer
from app.repos.hearout_records import HearoutRecordsRepo

_NOW = datetime(2026, 5, 25, 12, 0, 0, tzinfo=timezone.utc)
_TENANT = Tenant(sector="sector_a", unit="unit_1")


# ---------------------------------------------------------------------------
# Fake LLM client
# ---------------------------------------------------------------------------

class _FakeLLM:
    """Scripted LLM stub: returns pre-defined responses per call index."""

    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self._responses = responses
        self._call_index = 0
        self.chat = self  # type: ignore[assignment]
        self.completions = self  # type: ignore[assignment]

    async def create(self, **kwargs: Any) -> Any:
        resp = self._responses[self._call_index % len(self._responses)]
        self._call_index += 1
        msg = MagicMock()
        import json
        msg.content = json.dumps(resp)
        choice = MagicMock()
        choice.message = msg
        result = MagicMock()
        result.choices = [choice]
        return result


def _make_repo() -> HearoutRecordsRepo:
    """In-memory repo without real Cosmos."""
    mem = InMemoryContainer()

    class _SimpleRepo:
        """Minimal repo that works with InMemoryContainer."""

        def __init__(self) -> None:
            self._store: dict[str, dict[str, Any]] = {}

        async def upsert(
            self, record: HearoutRecord, extra_state: Optional[dict[str, Any]] = None
        ) -> HearoutRecord:
            doc: dict[str, Any] = record.model_dump(mode="json")
            if extra_state:
                doc.update(extra_state)
            self._store[record.id] = doc
            return record

        async def get(self, record_id: str, pk: str) -> Optional[HearoutRecord]:
            doc = self._store.get(record_id)
            if doc is None:
                return None
            allowed = set(HearoutRecord.model_fields.keys())
            clean = {k: v for k, v in doc.items() if k in allowed}
            return HearoutRecord.model_validate(clean)

        async def get_raw(self, record_id: str, pk: str) -> Optional[dict[str, Any]]:
            return self._store.get(record_id)

        async def get_by_session(self, session_id: str, pk: str) -> Optional[dict[str, Any]]:
            return self._store.get(session_id)

    return _SimpleRepo()  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
async def test_skip_produces_skipped_outcome() -> None:
    """SKIP answer → outcome=skipped, partial record persisted."""
    llm_responses = [
        # start() call
        {
            "slots": {"who": None, "what": None, "when": None, "where": None, "why": None, "how": None},
            "next_question": "誰がそれを行いましたか？",
            "complete": False,
            "self_critic": 3.0,
            "chat_extract_summary": "",
        },
    ]
    repo = _make_repo()
    agent = HearoutAgent(hearout_repo=repo, llm_client=_FakeLLM(llm_responses))  # type: ignore[arg-type]

    turn = await agent.start(gap_event_id="gap_001", user_id="user_A", tenant=_TENANT)
    assert turn.status == "in_progress"

    skipped_record = await agent.skip(turn.session_id)
    assert skipped_record.outcome == "skipped"


@pytest.mark.unit
async def test_skip_respond_produces_skipped_outcome() -> None:
    """respond('SKIP') → outcome=skipped."""
    llm_start = {
        "slots": {},
        "next_question": "最初の質問",
        "complete": False,
        "self_critic": 4.0,
        "chat_extract_summary": "",
    }
    repo = _make_repo()
    agent = HearoutAgent(hearout_repo=repo, llm_client=_FakeLLM([llm_start]))  # type: ignore[arg-type]

    turn = await agent.start(gap_event_id="gap_002", user_id="user_B", tenant=_TENANT)
    result = await agent.respond(turn.session_id, "SKIP")

    assert result.status == "skipped"
    assert result.final_record is not None
    assert result.final_record.outcome == "skipped"


@pytest.mark.unit
async def test_five_turn_limit_produces_expired() -> None:
    """5 respond() calls without LLM signaling complete → outcome=expired."""
    incomplete_response = {
        "slots": {"who": "田中"},
        "next_question": "次の質問",
        "complete": False,
        "self_critic": 5.0,
        "chat_extract_summary": "",
    }
    # start() + 5 respond() calls = 6 LLM calls; all return incomplete
    repo = _make_repo()
    agent = HearoutAgent(
        hearout_repo=repo,
        llm_client=_FakeLLM([incomplete_response] * 10),  # type: ignore[arg-type]
    )

    turn = await agent.start(gap_event_id="gap_003", user_id="user_C", tenant=_TENANT)
    session_id = turn.session_id

    result = turn
    for _ in range(5):
        if result.status != "in_progress":
            break
        result = await agent.respond(session_id, "まだわかりません")

    assert result.status == "expired"
    assert result.final_record is not None
    assert result.final_record.outcome == "expired"


@pytest.mark.unit
async def test_completed_when_llm_signals_complete() -> None:
    """When LLM returns complete=True → outcome=completed."""
    complete_response = {
        "slots": {"who": "田中", "what": "承認", "when": "月曜", "where": None, "why": None, "how": None},
        "next_question": None,
        "complete": True,
        "self_critic": 8.0,
        "chat_extract_summary": "田中が月曜日に承認した",
    }
    start_response = {
        "slots": {},
        "next_question": "誰が承認しましたか？",
        "complete": False,
        "self_critic": 5.0,
        "chat_extract_summary": "",
    }
    repo = _make_repo()
    agent = HearoutAgent(
        hearout_repo=repo,
        llm_client=_FakeLLM([start_response, complete_response]),  # type: ignore[arg-type]
    )

    turn = await agent.start(gap_event_id="gap_004", user_id="user_D", tenant=_TENANT)
    result = await agent.respond(turn.session_id, "田中さんが月曜日に承認しました")

    assert result.status == "completed"
    assert result.final_record is not None
    assert result.final_record.outcome == "completed"


@pytest.mark.unit
async def test_slot_clearing_on_negative_response() -> None:
    """Simulates ChatExtract rejection: if user contradicts, slots should be
    cleared on the next LLM call (complete=False, slots={}).

    This tests the state-machine contract: after a negative answer, the agent
    continues the interview (in_progress) with cleared slots, not the old ones.

    NOTE: The actual 'slot-clear on contradiction' is LLM-driven — the agent
    passes the transcript (including the negative answer) to the LLM, which
    returns empty slots. This test verifies the agent honours whatever slots
    the LLM returns, including an empty dict.
    """
    initial_response = {
        "slots": {"who": "山田", "what": "発注"},
        "next_question": "この理解で正しいですか？",
        "complete": False,
        "self_critic": 6.0,
        "chat_extract_summary": "山田が発注を行った",
    }
    # User says "違う" → LLM clears slots
    cleared_response = {
        "slots": {},
        "next_question": "では、誰が行いましたか？",
        "complete": False,
        "self_critic": 4.0,
        "chat_extract_summary": "",
    }
    repo = _make_repo()
    agent = HearoutAgent(
        hearout_repo=repo,
        llm_client=_FakeLLM([initial_response, cleared_response]),  # type: ignore[arg-type]
    )

    turn = await agent.start(gap_event_id="gap_005", user_id="user_E", tenant=_TENANT)
    # User negates the ChatExtract summary
    result = await agent.respond(turn.session_id, "違う、それは正しくない")

    # Still in progress — LLM returned cleared slots
    assert result.status == "in_progress"
    # Confirm that the cached state in _mem_cache has empty slots
    state = agent._mem_cache.get(turn.session_id)
    assert state is not None
    assert state.slots == {}, "Slots must be cleared after negative ChatExtract response"
