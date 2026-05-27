"""Review queues + decision endpoints (Req 9, 10, 17.7)."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api._deps import (
    current_reviewer_id,
    current_reviewer_scope,
    get_formalization_agent,
    get_formalization_queue_repo,
)
from app.contracts.agents import (
    ConflictResolution,
    CorpusUpsertResult,
    FormalizationAgentI,
)
from app.contracts.common import ConflictDecision, ReviewDecision, Tenant, utcnow
from app.contracts.cosmos import FormalizationTicket
from app.contracts.http import ConflictDecisionRequest, ReviewDecisionRequest
from app.util.telemetry import emit_metric

router = APIRouter(prefix="/reviews", tags=["reviews"])
logger = logging.getLogger(__name__)

LOCK_TTL_SECONDS = 300  # 5 minutes (Req 9.10)
PRIORITY_MEDIAN_THRESHOLD_SEC = 180  # Req 9.11
SELF_APPROVAL_WARN_THRESHOLD = 0.30  # Req 9.9


async def _list_tickets(
    *,
    statuses: tuple[str, ...],
    scope: list[Tenant],
    priority_only: bool,
) -> list[FormalizationTicket]:
    """Aggregate tickets across the reviewer's tenant scope.

    Cosmos can't cross-partition cheaply, so iterate per-tenant. ``statuses``
    picks the queue family: ``conflict_pending`` → ``list_conflict``,
    everything else → ``list_pending`` (covers ``pending_review`` +
    ``in_review`` per repo contract).
    """
    repo = get_formalization_queue_repo()
    if repo is None or not scope:
        return []
    is_conflict = "conflict_pending" in statuses
    out: list[FormalizationTicket] = []
    for tenant in scope:
        pk = tenant.pk
        tickets = (
            await repo.list_conflict(pk)
            if is_conflict
            else await repo.list_pending(pk)
        )
        out.extend(tickets)
    out.sort(key=lambda t: t.created_at)
    if priority_only:
        # Req 9.11 priority mode = surface high-weight tickets first.
        # Ticket model has no explicit priority flag; proxy by weight_final.
        out.sort(key=lambda t: t.weight_final, reverse=True)
    return out


async def _lock_ticket(
    ticket_id: str, reviewer_id: str
) -> dict[str, str]:
    """TODO(wt-b-import): atomic Cosmos patch with optimistic concurrency.

    Raise 409 if currently locked by a different reviewer & lock not expired.
    """
    expires = utcnow() + timedelta(seconds=LOCK_TTL_SECONDS)
    logger.info(
        "review.lock",
        extra={"ticket_id": ticket_id, "reviewer_id": reviewer_id},
    )
    return {"locked_until": expires.isoformat()}


async def _unlock_ticket(ticket_id: str, reviewer_id: str) -> None:
    logger.info(
        "review.unlock",
        extra={"ticket_id": ticket_id, "reviewer_id": reviewer_id},
    )


async def _self_approval_rate(reviewer_id: str) -> float:
    """7-day rolling self-approval rate (Req 9.9)."""
    # TODO(wt-b-import): query formalization_queue + dialogue_turns.
    _ = reviewer_id
    return 0.0


async def _median_review_minutes(scope: list[Tenant]) -> float:
    """Req 9.11 priority-mode trigger."""
    _ = scope
    return 0.0


def _effective_scope(
    scope: list[Tenant], sector: str | None, unit: str | None
) -> list[Tenant]:
    """In dev/local Easy Auth headers are absent so ``scope`` is empty.
    Allow callers to pass ``sector``/``unit`` query params as a fallback so
    UAT and the dev UI can list tickets for a specific tenant.
    """
    if scope:
        return scope
    if sector and unit:
        return [Tenant(sector=sector, unit=unit)]
    return []


@router.get("", response_model=list[FormalizationTicket])
async def list_reviews(
    priority_only: bool = Query(default=False),
    sector: str | None = Query(default=None),
    unit: str | None = Query(default=None),
    scope: Annotated[list[Tenant], Depends(current_reviewer_scope)] = [],
) -> list[FormalizationTicket]:
    return await _list_tickets(
        statuses=("pending_review",),
        scope=_effective_scope(scope, sector, unit),
        priority_only=priority_only,
    )


@router.get("/conflict", response_model=list[FormalizationTicket])
async def list_conflict_reviews(
    sector: str | None = Query(default=None),
    unit: str | None = Query(default=None),
    scope: Annotated[list[Tenant], Depends(current_reviewer_scope)] = [],
) -> list[FormalizationTicket]:
    return await _list_tickets(
        statuses=("conflict_pending",),
        scope=_effective_scope(scope, sector, unit),
        priority_only=False
    )


@router.get("/self-approval", response_model=dict)
async def self_approval_dashboard(
    reviewer_id: Annotated[str, Depends(current_reviewer_id)],
) -> dict[str, Any]:
    rate = await _self_approval_rate(reviewer_id)
    return {
        "reviewer_id": reviewer_id,
        "rate_7d": rate,
        "warn": rate > SELF_APPROVAL_WARN_THRESHOLD,
        "threshold": SELF_APPROVAL_WARN_THRESHOLD,
    }


@router.get("/priority-mode", response_model=dict)
async def priority_mode(
    scope: Annotated[list[Tenant], Depends(current_reviewer_scope)] = [],
) -> dict[str, Any]:
    median_sec = await _median_review_minutes(scope)
    return {
        "median_sec": median_sec,
        "active": median_sec > PRIORITY_MEDIAN_THRESHOLD_SEC,
        "threshold_sec": PRIORITY_MEDIAN_THRESHOLD_SEC,
    }


@router.post("/{ticket_id}/lock")
async def lock_review(
    ticket_id: str,
    reviewer_id: Annotated[str, Depends(current_reviewer_id)],
) -> dict[str, str]:
    return await _lock_ticket(ticket_id, reviewer_id)


@router.post("/{ticket_id}/unlock")
async def unlock_review(
    ticket_id: str,
    reviewer_id: Annotated[str, Depends(current_reviewer_id)],
) -> dict[str, bool]:
    await _unlock_ticket(ticket_id, reviewer_id)
    return {"ok": True}


@router.post("/{ticket_id}/decision", response_model=CorpusUpsertResult)
async def decide_review(
    ticket_id: str,
    body: ReviewDecisionRequest,
    sector: str,
    unit: str,
    agent: Annotated[FormalizationAgentI, Depends(get_formalization_agent)],
    reviewer_id: Annotated[str, Depends(current_reviewer_id)] = "",
) -> CorpusUpsertResult:
    pk = Tenant(sector=sector, unit=unit).pk
    decision: ReviewDecision = body.decision  # type: ignore[assignment]
    if decision not in ("approve", "edit", "reject"):
        raise HTTPException(status_code=422, detail="invalid decision")
    try:
        result = await agent.on_review_decision(
            ticket_id=ticket_id, pk=pk, decision=decision, edited=None
        )
    except RuntimeError as exc:  # stub path
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    emit_metric(
        "review.decision",
        1,
        {
            "sector": sector,
            "unit": unit,
            "decision": decision,
            "reviewer_id": reviewer_id,
            "ticket_id": ticket_id,
        },
    )
    return result


@router.post("/{ticket_id}/conflict", response_model=ConflictResolution)
async def decide_conflict(
    ticket_id: str,
    body: ConflictDecisionRequest,
    sector: str,
    unit: str,
    agent: Annotated[FormalizationAgentI, Depends(get_formalization_agent)],
) -> ConflictResolution:
    pk = Tenant(sector=sector, unit=unit).pk
    decision: ConflictDecision = body.decision  # type: ignore[assignment]
    if decision not in ("adopt_new", "keep_existing", "coexist"):
        raise HTTPException(status_code=422, detail="invalid conflict decision")
    try:
        return await agent.on_conflict_decision(
            ticket_id=ticket_id, pk=pk, decision=decision
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
