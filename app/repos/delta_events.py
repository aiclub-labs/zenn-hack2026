"""Cosmos repo for `delta_events` (Req 12).

Append-only ledger of gap-detection decisions. Cooldown lookup keyed by
`schema_field_id` within the partition; session scope is enforced at the
agent layer (Delta Detector pulls recent turn ids for the session and asks
for matching delta_events).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from azure.cosmos.aio import ContainerProxy
from azure.cosmos.exceptions import CosmosResourceNotFoundError

from app.contracts.cosmos import DeltaEvent

_COOLDOWN_DAYS = 7


class DeltaEventsRepo:
    container_name = "delta_events"

    def __init__(self, container: ContainerProxy) -> None:
        self._c = container

    async def append(self, event: DeltaEvent) -> DeltaEvent:
        await self._c.upsert_item(event.model_dump(mode="json"))
        return event

    async def get(self, event_id: str, pk: str) -> Optional[DeltaEvent]:
        """Point-read a single delta event by id (used by Merge-B resolvers)."""
        try:
            doc = await self._c.read_item(item=event_id, partition_key=pk)
        except CosmosResourceNotFoundError:
            return None
        return DeltaEvent.model_validate(doc)

    async def list_recent_for_session(
        self,
        pk: str,
        turn_ids: list[str],
        schema_field_id: Optional[str] = None,
        limit: int = 50,
    ) -> list[DeltaEvent]:
        """Return delta_events whose `turn_id` is in `turn_ids` (caller-supplied
        recent-turn window for the active session)."""
        if not turn_ids:
            return []
        # IN-clause with parameterized values
        placeholders = ",".join(f"@t{i}" for i in range(len(turn_ids)))
        params: list[dict[str, Any]] = [{"name": "@pk", "value": pk}]
        for i, tid in enumerate(turn_ids):
            params.append({"name": f"@t{i}", "value": tid})
        query = (
            f"SELECT TOP {int(limit)} * FROM c WHERE c.pk = @pk "
            f"AND c.turn_id IN ({placeholders})"
        )
        if schema_field_id:
            query += " AND c.schema_field_id = @fid"
            params.append({"name": "@fid", "value": schema_field_id})
        query += " ORDER BY c._ts DESC"
        items: list[DeltaEvent] = []
        async for it in self._c.query_items(
            query=query, parameters=params, partition_key=pk
        ):
            items.append(DeltaEvent.model_validate(it))
        return items

    async def get_cooldown(
        self, pk: str, schema_field_id: str
    ) -> Optional[datetime]:
        """Return the latest cooldown_until > now for (pk, schema_field_id), if any."""
        query = (
            "SELECT TOP 1 c.cooldown_until FROM c WHERE c.pk = @pk "
            "AND c.schema_field_id = @fid AND IS_DEFINED(c.cooldown_until) "
            "ORDER BY c._ts DESC"
        )
        params = [
            {"name": "@pk", "value": pk},
            {"name": "@fid", "value": schema_field_id},
        ]
        async for it in self._c.query_items(
            query=query, parameters=params, partition_key=pk
        ):
            raw = it.get("cooldown_until")
            if not raw:
                return None
            ts = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if ts > datetime.now(timezone.utc):
                return ts
            return None
        return None

    @staticmethod
    def default_cooldown_until() -> datetime:
        return datetime.now(timezone.utc) + timedelta(days=_COOLDOWN_DAYS)
