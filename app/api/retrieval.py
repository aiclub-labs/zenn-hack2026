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
    from app.util.embedding import embed as _real_embed

    return await _real_embed(text)


async def _aisearch_query(
    tenant: Tenant, vector: list[float], top_k: int = 8
) -> list[dict[str, Any]]:
    from app.util.aisearch import CorpusIndex

    raw = await CorpusIndex().query(
        tenant=tenant, query_vec=vector, top_k=top_k, shareability_min="private"
    )
    out: list[dict[str, Any]] = []
    for h in raw:
        out.append(
            {
                "record_id": h.get("id", ""),
                "schema_field_id": h.get("schema_field_id", "") or "",
                "weight": float(h.get("weight_final", 0.0) or 0.0),
                "superseded_by": h.get("superseded_by") or None,
                "content": h.get("content", "") or "",
            }
        )
    return out


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
) -> tuple[list[CitationRef], list[dict[str, Any]], list[dict[str, Any]]]:
    """Top-k retrieval + activation-time conflict detection.

    Conflict: >=2 distinct record viewpoints under one schema_field_id.
    Returns (citations, conflicts, prompt_ctx) where prompt_ctx is the
    [{citation_id, snippet}] list consumed by the AOAI system prompt.
    """
    vec = await _embed(query)
    hits = await _aisearch_query(tenant, vec)

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    citations: list[CitationRef] = []
    prompt_ctx: list[dict[str, Any]] = []
    for h in hits:
        sfid = str(h["schema_field_id"])
        rid = str(h["record_id"])
        grouped[sfid].append(h)
        citations.append(
            CitationRef(
                record_id=rid,
                schema_field_id=sfid,
                weight=float(h.get("weight", 0.0)),
                superseded_by=h.get("superseded_by"),
            )
        )
        prompt_ctx.append(
            {"citation_id": rid, "snippet": str(h.get("content", ""))[:300]}
        )

    conflicts: list[dict[str, Any]] = []
    for sfid, group in grouped.items():
        distinct = {g["record_id"] for g in group}
        if len(distinct) >= 2:
            conflicts.append({"schema_field_id": sfid, "alt_count": len(distinct)})
            await _log_truth_judgment_activation(tenant, sfid, sorted(distinct))

    _ = user_id  # reserved for personalization / audit
    return citations, conflicts, prompt_ctx


@router.get("/retrieve", response_model=RetrieveResponse)
async def get_retrieve(
    sector: str,
    unit: str,
    q: str = Query(..., min_length=1),
    user_id: str = "anonymous",
) -> RetrieveResponse:
    tenant = Tenant(sector=sector, unit=unit)
    records, conflicts, _ = await retrieve_for_turn(
        tenant=tenant, query=q, user_id=user_id
    )
    return RetrieveResponse(records=records, conflicts=conflicts)
