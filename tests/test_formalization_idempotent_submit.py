"""Regression test for Issue #36 — expired hearout → /respond → duplicate ticket.

When a client (re-)submits a HearoutRecord that has already produced a
formalization_queue ticket, ``submit_for_review`` must upsert the same row
(deterministic ticket_id keyed by ``hearout_id``) and refuse to resurrect
tickets that have already moved past intake.
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.formalization.agent import FormalizationAgent
from app.contracts.cosmos import FormalizationTicket, HearoutRecord


def _record() -> HearoutRecord:
    return HearoutRecord(
        id="hr_test_1",
        pk="sector_a#unit_1",
        session_id="s1",
        gap_event_id="ge_1",
        transcript=[],
        turn_count=5,
        outcome="completed",
        who=None, what="x", when=None, where=None, why=None, how=None,
    )


def _build_agent(queue_mock, hearout_mock) -> FormalizationAgent:
    return FormalizationAgent(
        queue_repo=queue_mock,
        hearout_repo=hearout_mock,
        corpus_meta_repo=MagicMock(),
        citation_audit_repo=MagicMock(),
        delta_events_repo=MagicMock(),
        corpus=MagicMock(),
        truth_judgment=MagicMock(judge=AsyncMock()),
        notifier=MagicMock(emit=AsyncMock()),
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_submit_for_review_is_idempotent_by_hearout_id() -> None:
    record = _record()
    queue = MagicMock()
    queue.upsert = AsyncMock()
    queue.get = AsyncMock(return_value=None)
    hearout = MagicMock(get_raw=AsyncMock(return_value=None))
    agent = _build_agent(queue, hearout)

    t1 = await agent.submit_for_review(
        record=record, weights=(2.0, 1.0, 1.0, 0.2), tj_verdict=None
    )
    t2 = await agent.submit_for_review(
        record=record, weights=(2.0, 1.0, 1.0, 0.2), tj_verdict=None
    )
    assert t1.id == t2.id == "ft_hr_test_1"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_submit_does_not_resurrect_post_intake_ticket() -> None:
    record = _record()
    existing = FormalizationTicket(
        id="ft_hr_test_1",
        pk=record.pk,
        hearout_id=record.id,
        weight_a=2.0, weight_b=1.0, weight_c=1.0, weight_final=0.2,
        tj_verdict=None,
        status="approved",
        locked_by=None, lock_expires_at=None,
        reviewer_id="rv_1", decision="approve",
        conflict_decision=None, edit_diff=None, expired_at=None,
        created_at=datetime(2026, 5, 28, tzinfo=timezone.utc),
    )
    queue = MagicMock()
    queue.upsert = AsyncMock()
    queue.get = AsyncMock(return_value=existing)
    hearout = MagicMock(get_raw=AsyncMock(return_value=None))
    agent = _build_agent(queue, hearout)

    returned = await agent.submit_for_review(
        record=record, weights=(2.0, 1.0, 1.0, 0.2), tj_verdict=None
    )
    assert returned is existing
    queue.upsert.assert_not_called()
