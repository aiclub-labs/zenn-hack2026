"""Voting + ranking endpoints (consultant-tacit pivot, 2026-05-29).

Counters live on the corpus AI Search doc itself:
    upvotes, downvotes, score = upvotes - downvotes

POST /records/{record_id}/vote   {direction: "up"|"down"}
GET  /ranking?sector=&unit=&limit=

`score` is materialized at write time so the ranking endpoint sorts
server-side without a custom scoring profile. Read-modify-write is
non-atomic; concurrent votes can lose one — acceptable for demo-scale
ranking signal, same posture as record_referenced_count.
"""
from __future__ import annotations

import logging
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(tags=["votes"])
logger = logging.getLogger(__name__)


class VoteRequest(BaseModel):
    direction: Literal["up", "down"]


class VoteResponse(BaseModel):
    record_id: str
    upvotes: int
    downvotes: int
    score: int


class RankingEntry(BaseModel):
    record_id: str
    schema_field_id: str
    content: str
    upvotes: int
    downvotes: int
    score: int


class RecordDetail(BaseModel):
    record_id: str
    schema_field_id: str
    content: str
    atomic_claims: list[str]
    upvotes: int
    downvotes: int
    score: int
    referenced_count: int
    superseded_by: str | None = None


@router.get("/records/{record_id}", response_model=RecordDetail)
async def get_record(record_id: str) -> RecordDetail:
    from app.util.aisearch import CorpusIndex

    index = CorpusIndex()
    try:
        doc = await index._client.get_document(key=record_id)  # type: ignore[attr-defined]
    except Exception as exc:
        logger.warning("record.lookup_failed", extra={"record_id": record_id, "err": str(exc)})
        raise HTTPException(status_code=404, detail="record not found")
    superseded = doc.get("superseded_by") or None
    return RecordDetail(
        record_id=str(doc.get("id", record_id)),
        schema_field_id=str(doc.get("schema_field_id", "") or ""),
        content=str(doc.get("content", "") or ""),
        atomic_claims=list(doc.get("atomic_claims") or []),
        upvotes=int(doc.get("upvotes") or 0),
        downvotes=int(doc.get("downvotes") or 0),
        score=int(doc.get("score") or 0),
        referenced_count=int(doc.get("record_referenced_count") or 0),
        superseded_by=superseded if superseded else None,
    )


class RankingResponse(BaseModel):
    entries: list[RankingEntry]


@router.post("/records/{record_id}/vote", response_model=VoteResponse)
async def cast_vote(record_id: str, body: VoteRequest) -> VoteResponse:
    from app.util.aisearch import CorpusIndex

    index = CorpusIndex()
    try:
        doc: dict[str, Any] = await index._client.get_document(key=record_id)  # type: ignore[attr-defined]
    except Exception as exc:
        logger.warning("vote.lookup_failed", extra={"record_id": record_id, "err": str(exc)})
        raise HTTPException(status_code=404, detail="record not found")

    up = int(doc.get("upvotes") or 0)
    down = int(doc.get("downvotes") or 0)
    if body.direction == "up":
        up += 1
    else:
        down += 1
    score = up - down

    try:
        await index._client.merge_or_upload_documents(  # type: ignore[attr-defined]
            documents=[
                {
                    "id": record_id,
                    "pk": doc.get("pk", ""),
                    "upvotes": up,
                    "downvotes": down,
                    "score": score,
                }
            ]
        )
    except Exception as exc:
        logger.warning("vote.write_failed", extra={"record_id": record_id, "err": str(exc)})
        raise HTTPException(status_code=502, detail="vote write failed")

    return VoteResponse(record_id=record_id, upvotes=up, downvotes=down, score=score)


@router.get("/ranking", response_model=RankingResponse)
async def get_ranking(
    sector: str,
    unit: str,
    limit: int = Query(20, ge=1, le=100),
) -> RankingResponse:
    from app.util.aisearch import CorpusIndex

    index = CorpusIndex()
    filter_expr = (
        f"sector eq '{sector}' and unit eq '{unit}' "
        "and is_active eq true "
        "and (superseded_by eq null or superseded_by eq '')"
    )
    try:
        results = await index._client.search(  # type: ignore[attr-defined]
            search_text="*",
            filter=filter_expr,
            order_by=["score desc"],
            top=limit,
            select=[
                "id",
                "schema_field_id",
                "content",
                "upvotes",
                "downvotes",
                "score",
            ],
        )
    except Exception as exc:
        logger.warning("ranking.query_failed", extra={"err": str(exc)})
        raise HTTPException(status_code=502, detail="ranking query failed")

    entries: list[RankingEntry] = []
    async for h in results:
        entries.append(
            RankingEntry(
                record_id=str(h.get("id", "")),
                schema_field_id=str(h.get("schema_field_id", "") or ""),
                content=str(h.get("content", "") or ""),
                upvotes=int(h.get("upvotes") or 0),
                downvotes=int(h.get("downvotes") or 0),
                score=int(h.get("score") or 0),
            )
        )
    return RankingResponse(entries=entries)
