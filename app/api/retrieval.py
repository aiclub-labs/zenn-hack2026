"""GET /retrieve + retrieve_for_turn helper (Req 6, 8)."""
from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from fastapi import APIRouter, Query

from app.contracts.common import Tenant
from app.contracts.http import CitationRef, RetrieveResponse

router = APIRouter(tags=["retrieval"])
logger = logging.getLogger(__name__)


async def _embed(text: str) -> list[float]:
    """TODO(wt-d-import): replace with ``app.util.embedding.embed``."""
    return [0.0] * 8


async def _aisearch_query(
    tenant: Tenant, vector: list[float], top_k: int = 8
) -> list[dict[str, Any]]:
    """TODO(wt-d-import): replace with ``app.util.aisearch.CorpusIndex.query``.

    Real impl filters by partition (pk = sector#unit), shareability
    (private/unit/public), is_active=true, superseded_by is null.
    Returns hits with ``{record_id, schema_field_id, weight,
    superseded_by, content}``.
    """
    return []


async def _log_truth_judgment_activation(
    tenant: Tenant, schema_field_id: str, record_ids: list[str]
) -> None:
    """activation-time TJ log when retrieval surfaces conflicting views."""
    logger.info(
        "tj.activation_time",
        extra={
            "pk": tenant.pk,
            "schema_field_id": schema_field_id,
            "record_ids": record_ids,
        },
    )
    # TODO(wt-d-import): TruthJudgmentLogRepo.append(pattern="activation-time")


async def retrieve_for_turn(
    *, tenant: Tenant, query: str, user_id: str
) -> tuple[list[CitationRef], list[dict[str, Any]]]:
    """Top-k retrieval + activation-time conflict detection.

    Conflict: >=2 distinct record viewpoints under one schema_field_id.
    """
    vec = await _embed(query)
    hits = await _aisearch_query(tenant, vec)

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    citations: list[CitationRef] = []
    for h in hits:
        sfid = str(h["schema_field_id"])
        grouped[sfid].append(h)
        citations.append(
            CitationRef(
                record_id=str(h["record_id"]),
                schema_field_id=sfid,
                weight=float(h.get("weight", 0.0)),
                superseded_by=h.get("superseded_by"),
            )
        )

    conflicts: list[dict[str, Any]] = []
    for sfid, group in grouped.items():
        distinct = {g["record_id"] for g in group}
        if len(distinct) >= 2:
            conflicts.append({"schema_field_id": sfid, "alt_count": len(distinct)})
            await _log_truth_judgment_activation(tenant, sfid, sorted(distinct))

    _ = user_id  # reserved for personalization / audit
    return citations, conflicts


@router.get("/retrieve", response_model=RetrieveResponse)
async def get_retrieve(
    sector: str,
    unit: str,
    q: str = Query(..., min_length=1),
    user_id: str = "anonymous",
) -> RetrieveResponse:
    tenant = Tenant(sector=sector, unit=unit)
    records, conflicts = await retrieve_for_turn(
        tenant=tenant, query=q, user_id=user_id
    )
    return RetrieveResponse(records=records, conflicts=conflicts)
