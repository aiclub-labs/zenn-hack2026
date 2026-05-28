"""Cosmos repo for the ``schema_audit_log`` container (append-only)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.contracts.cosmos import SchemaAuditEntry

from ._base import ContainerLike


class SchemaAuditLogRepo:
    def __init__(self, container: ContainerLike) -> None:
        self._c = container

    async def append(self, entry: SchemaAuditEntry) -> SchemaAuditEntry:
        await self._c.upsert_item(entry.model_dump(mode="json"))
        return entry

    async def list(
        self,
        pk: str,
        limit: int = 50,
        since: Optional[datetime] = None,
    ) -> list[SchemaAuditEntry]:
        query = "SELECT * FROM c WHERE c.pk = @pk ORDER BY c.changed_at DESC"
        params = [{"name": "@pk", "value": pk}]
        out: list[SchemaAuditEntry] = []
        it = self._c.query_items(
            query=query, parameters=params, partition_key=pk
        )
        async for raw in it:
            if raw.get("pk") != pk:
                continue
            entry = SchemaAuditEntry.model_validate(raw)
            if since is not None and entry.changed_at < since:
                continue
            out.append(entry)
        out.sort(key=lambda e: e.changed_at, reverse=True)
        return out[:limit]
