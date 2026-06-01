"""GET /citations/{id} — Req 6.4, 6.5."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from app.contracts.common import make_pk
from app.contracts.http import CitationDetail

router = APIRouter(prefix="/citations", tags=["citations"])
logger = logging.getLogger(__name__)

_SUPERSEDED_BANNER = "この見解は更新されています"


async def _load_corpus_meta(
    record_id: str, pk: str
) -> dict[str, Any] | None:
    """TODO(wt-b-import): CorpusMetaRepo.get(record_id, pk)."""
    return None


async def _increment_ref_count(record_id: str, pk: str) -> None:
    """TODO(wt-b-import): CorpusMetaRepo.bump_reference(record_id, pk)."""
    logger.info("corpus_meta.ref++", extra={"record_id": record_id, "pk": pk})


@router.get("/{citation_id}", response_model=CitationDetail)
async def get_citation(
    citation_id: str, sector: str, unit: str
) -> CitationDetail:
    pk = make_pk(sector, unit)
    meta = await _load_corpus_meta(citation_id, pk)
    if meta is None:
        # Demo fallback so UI works pre-DB:
        return CitationDetail(
            record_id=citation_id,
            content="（demo）参照本文がまだ実装されていません",
            schema_field_id="unknown",
            superseded_by=None,
            superseded_banner=None,
        )
    superseded_by = meta.get("superseded_by")
    await _increment_ref_count(citation_id, pk)
    return CitationDetail(
        record_id=citation_id,
        content=str(meta.get("content", "")),
        schema_field_id=str(meta.get("schema_field_id", "unknown")),
        superseded_by=superseded_by,
        superseded_banner=_SUPERSEDED_BANNER if superseded_by else None,
    )
