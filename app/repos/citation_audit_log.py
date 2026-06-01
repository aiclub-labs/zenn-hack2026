"""Cosmos repo for `citation_audit_log` (Req 10.8)."""
from __future__ import annotations

from typing import Any

from azure.cosmos.aio import ContainerProxy

from app.contracts.cosmos import CitationAuditEntry


class CitationAuditLogRepo:
    container_name = "citation_audit_log"

    def __init__(self, container: ContainerProxy) -> None:
        self._c = container

    async def append(self, entry: CitationAuditEntry) -> CitationAuditEntry:
        await self._c.upsert_item(entry.model_dump(mode="json"))
        return entry

    async def list_for_record(
        self, pk: str, record_id: str, limit: int = 50
    ) -> list[CitationAuditEntry]:
        query = (
            f"SELECT TOP {int(limit)} * FROM c WHERE c.pk = @pk AND "
            "(c.old_record_id = @rid OR c.new_record_id = @rid) "
            "ORDER BY c.occurred_at DESC"
        )
        params: list[dict[str, Any]] = [
            {"name": "@pk", "value": pk},
            {"name": "@rid", "value": record_id},
        ]
        out: list[CitationAuditEntry] = []
        async for it in self._c.query_items(
            query=query, parameters=params, partition_key=pk
        ):
            out.append(CitationAuditEntry.model_validate(it))
        return out
