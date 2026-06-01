"""Cosmos repo for the ``schemas`` container.

WT-B owns container wiring; WT-C contributes upsert/list/get used by the
Schema Manager agent. All additions here are additive — append-only API.
"""
from __future__ import annotations

from typing import Optional

from app.contracts.cosmos import SchemaFieldDoc

from ._base import ContainerLike


class SchemasRepo:
    """Thin wrapper over the ``schemas`` Cosmos container."""

    def __init__(self, container: ContainerLike) -> None:
        self._c = container

    async def upsert(self, field: SchemaFieldDoc) -> SchemaFieldDoc:
        body = field.model_dump(mode="json")
        await self._c.upsert_item(body)
        return field

    async def get(self, field_id: str, pk: str) -> Optional[SchemaFieldDoc]:
        try:
            raw = await self._c.read_item(item=field_id, partition_key=pk)
        except Exception:
            return None
        return SchemaFieldDoc.model_validate(raw)

    async def list_active(self, pk: str) -> list[SchemaFieldDoc]:
        query = (
            "SELECT * FROM c WHERE c.pk = @pk AND c.is_active = true "
            "ORDER BY c.field_name ASC"
        )
        params = [{"name": "@pk", "value": pk}]
        out: list[SchemaFieldDoc] = []
        it = self._c.query_items(
            query=query, parameters=params, partition_key=pk
        )
        async for raw in it:
            # In-memory fallback returns all rows; filter defensively.
            if raw.get("pk") != pk or not raw.get("is_active", True):
                continue
            out.append(SchemaFieldDoc.model_validate(raw))
        return out

    async def list(
        self, pk: str, active_only: bool = True
    ) -> list[SchemaFieldDoc]:
        """Return schema fields for a tenant.

        ``active_only=True`` mirrors :meth:`list_active`; ``False`` returns the
        full set including deactivated rows (used by the Admin UI list).
        """
        if active_only:
            return await self.list_active(pk)
        return await self.list_all(pk)

    async def list_all(self, pk: str) -> list[SchemaFieldDoc]:
        query = "SELECT * FROM c WHERE c.pk = @pk"
        params = [{"name": "@pk", "value": pk}]
        out: list[SchemaFieldDoc] = []
        it = self._c.query_items(
            query=query, parameters=params, partition_key=pk
        )
        async for raw in it:
            if raw.get("pk") != pk:
                continue
            out.append(SchemaFieldDoc.model_validate(raw))
        return out

    async def latest_revision(self, field_id: str, pk: str) -> int:
        """Return current revision_id or 0 when absent."""
        doc = await self.get(field_id, pk)
        return doc.revision_id if doc else 0

    async def latest_revision_for_tenant(self, pk: str) -> int:
        """Return the max revision_id observed across all schema fields for a tenant."""
        docs = await self.list_all(pk)
        if not docs:
            return 0
        return max(d.revision_id for d in docs)

    async def list_unseen(self, pk: str, since_revision: int) -> list[SchemaFieldDoc]:
        """Return active schema fields with revision_id > since_revision."""
        docs = await self.list_all(pk)
        return [d for d in docs if d.revision_id > since_revision]
