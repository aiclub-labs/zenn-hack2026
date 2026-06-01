"""Cosmos repo for `corpus_meta` (Req 6, 10, 17.6).

Tracks reference counts, logical deletion (is_active), and conflict-resolution
relations (`superseded_by`, `coexisting_views`). Mirrors are also pushed into
AI Search by the Formalization Agent.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from azure.cosmos.aio import ContainerProxy
from azure.cosmos.exceptions import CosmosResourceNotFoundError

from app.contracts.cosmos import CorpusMeta


class CorpusMetaRepo:
    container_name = "corpus_meta"

    def __init__(self, container: ContainerProxy) -> None:
        self._c = container

    async def upsert(self, meta: CorpusMeta) -> CorpusMeta:
        await self._c.upsert_item(meta.model_dump(mode="json"))
        return meta

    async def get(self, meta_id: str, pk: str) -> Optional[CorpusMeta]:
        try:
            doc = await self._c.read_item(item=meta_id, partition_key=pk)
        except CosmosResourceNotFoundError:
            return None
        return CorpusMeta.model_validate(doc)

    async def increment_referenced(self, meta_id: str, pk: str) -> Optional[CorpusMeta]:
        meta = await self.get(meta_id, pk)
        if meta is None:
            return None
        doc = meta.model_dump(mode="json")
        doc["referenced_count"] = int(doc.get("referenced_count", 0)) + 1
        doc["last_referenced_at"] = datetime.now(timezone.utc).isoformat()
        await self._c.upsert_item(doc)
        return CorpusMeta.model_validate(doc)

    async def set_superseded(
        self, meta_id: str, pk: str, superseded_by: str
    ) -> Optional[CorpusMeta]:
        meta = await self.get(meta_id, pk)
        if meta is None:
            return None
        doc = meta.model_dump(mode="json")
        doc["superseded_by"] = superseded_by
        doc["is_active"] = False
        await self._c.upsert_item(doc)
        return CorpusMeta.model_validate(doc)

    async def add_coexisting(
        self, meta_id: str, pk: str, peer_ids: list[str]
    ) -> Optional[CorpusMeta]:
        meta = await self.get(meta_id, pk)
        if meta is None:
            return None
        doc: dict[str, Any] = meta.model_dump(mode="json")
        current: list[str] = list(doc.get("coexisting_views") or [])
        merged = sorted({*current, *peer_ids} - {meta_id})
        doc["coexisting_views"] = merged
        await self._c.upsert_item(doc)
        return CorpusMeta.model_validate(doc)
