"""Cosmos repo for `schema_candidate_log` (Req 12.9-12.10).

LLM-suggested 'maybe a new schema field' notes from Delta Detector when the
turn doesn't match any active schema. Dedupes by `suggested_field_hint`
within the partition.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Optional

from azure.cosmos.aio import ContainerProxy
from azure.cosmos.exceptions import CosmosResourceNotFoundError

from app.contracts.cosmos import SchemaCandidate


def _candidate_id(pk: str, hint: str) -> str:
    h = hashlib.sha1(f"{pk}::{hint}".encode("utf-8")).hexdigest()
    return f"sc_{h[:24]}"


class SchemaCandidateLogRepo:
    container_name = "schema_candidate_log"

    def __init__(self, container: ContainerProxy) -> None:
        self._c = container

    async def upsert(
        self,
        pk: str,
        turn_id: str,
        suggested_field_hint: str,
        llm_reason: str,
    ) -> SchemaCandidate:
        cid = _candidate_id(pk, suggested_field_hint)
        try:
            doc: dict[str, Any] = await self._c.read_item(item=cid, partition_key=pk)
            doc["occurrences"] = int(doc.get("occurrences", 0)) + 1
            doc["last_seen_at"] = datetime.now(timezone.utc).isoformat()
            doc["turn_id"] = turn_id
            doc["llm_reason"] = llm_reason
        except CosmosResourceNotFoundError:
            doc = SchemaCandidate(
                id=cid,
                pk=pk,
                turn_id=turn_id,
                suggested_field_hint=suggested_field_hint,
                llm_reason=llm_reason,
                occurrences=1,
                last_seen_at=datetime.now(timezone.utc),
            ).model_dump(mode="json")
        await self._c.upsert_item(doc)
        return SchemaCandidate.model_validate(doc)

    async def list(
        self, pk: str, limit: int = 50, min_occurrences: Optional[int] = None
    ) -> list[SchemaCandidate]:
        query = f"SELECT TOP {int(limit)} * FROM c WHERE c.pk = @pk"
        params: list[dict[str, Any]] = [{"name": "@pk", "value": pk}]
        if min_occurrences is not None:
            query += " AND c.occurrences >= @mo"
            params.append({"name": "@mo", "value": min_occurrences})
        query += " ORDER BY c.last_seen_at DESC"
        out: list[SchemaCandidate] = []
        async for it in self._c.query_items(
            query=query, parameters=params, partition_key=pk
        ):
            out.append(SchemaCandidate.model_validate(it))
        return out
