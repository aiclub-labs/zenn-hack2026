"""POST /hearout/{start|{session}/respond|{session}/skip} — Req 5."""
from __future__ import annotations

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException

from app.api._deps import get_formalization_agent, get_hearout_agent
from app.contracts.agents import FormalizationAgentI, HearoutAgentI, HearoutTurn
from app.contracts.common import Tenant
from app.contracts.cosmos import HearoutRecord
from app.contracts.http import HearoutRespondRequest, HearoutStartRequest

router = APIRouter(prefix="/hearout", tags=["hearout"])
logger = logging.getLogger(__name__)


async def _maybe_submit(
    formalization: FormalizationAgentI, record: Optional[HearoutRecord]
) -> None:
    """When a hearout terminates, push its record onto the review queue.

    The hearout agent itself doesn't know about formalization, so the API
    layer wires the two together: any terminal HearoutRecord (completed /
    skipped / expired) triggers weight + submit_for_review. Errors are
    logged but not surfaced — a queue write failure shouldn't fail the
    user-visible hearout response.
    """
    if record is None:
        return
    try:
        weights = await formalization.weight(record)
        await formalization.submit_for_review(
            record=record, weights=weights, tj_verdict=None
        )
    except Exception as exc:  # pragma: no cover
        logger.warning("formalization.submit_for_review failed: %s", exc)


@router.post("/start", response_model=HearoutTurn)
async def start(
    body: HearoutStartRequest,
    agent: Annotated[HearoutAgentI, Depends(get_hearout_agent)],
    formalization: Annotated[
        FormalizationAgentI, Depends(get_formalization_agent)
    ],
) -> HearoutTurn:
    """Begin a hearout session triggered by a delta-detector gap.

    The returned ``HearoutTurn.session_id`` is the hearout record_id; the
    client must use it for subsequent ``/respond`` and ``/skip`` calls.
    """
    tenant = Tenant(sector=body.sector, unit=body.unit)
    try:
        turn = await agent.start(
            gap_event_id=body.gap_event_id,
            user_id=body.user_id,
            tenant=tenant,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    await _maybe_submit(formalization, turn.final_record)
    return turn


@router.post("/{session_id}/respond", response_model=HearoutTurn)
async def respond(
    session_id: str,
    body: HearoutRespondRequest,
    agent: Annotated[HearoutAgentI, Depends(get_hearout_agent)],
    formalization: Annotated[
        FormalizationAgentI, Depends(get_formalization_agent)
    ],
) -> HearoutTurn:
    try:
        turn = await agent.respond(session_id=session_id, answer=body.answer)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    await _maybe_submit(formalization, turn.final_record)
    return turn


@router.post("/{session_id}/skip", response_model=HearoutRecord)
async def skip(
    session_id: str,
    agent: Annotated[HearoutAgentI, Depends(get_hearout_agent)],
    formalization: Annotated[
        FormalizationAgentI, Depends(get_formalization_agent)
    ],
) -> HearoutRecord:
    try:
        record = await agent.skip(session_id=session_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    await _maybe_submit(formalization, record)
    return record
