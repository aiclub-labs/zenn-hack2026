"""Cosmos repo for `formalization_queue` (Req 9, 10, 11, 13).

Supports normal `pending_review` queue, `conflict_pending` queue,
5-minute lock TTL, and 24h SLA expiry scan.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from azure.cosmos.aio import ContainerProxy
from azure.cosmos.exceptions import CosmosResourceNotFoundError

from app.contracts.common import QueueStatus
from app.contracts.cosmos import FormalizationTicket

_DEFAULT_LOCK_TTL_S = 300
_SLA_HOURS = 24


class FormalizationQueueRepo:
    container_name = "formalization_queue"

    def __init__(self, container: ContainerProxy) -> None:
        self._c = container

    async def upsert(self, ticket: FormalizationTicket) -> FormalizationTicket:
        await self._c.upsert_item(ticket.model_dump(mode="json"))
        return ticket

    async def get(self, ticket_id: str, pk: str) -> Optional[FormalizationTicket]:
        try:
            doc = await self._c.read_item(item=ticket_id, partition_key=pk)
        except CosmosResourceNotFoundError:
            return None
        return FormalizationTicket.model_validate(doc)

    async def list_pending(
        self, pk: str, limit: int = 50
    ) -> list[FormalizationTicket]:
        return await self._list_by_status(pk, ["pending_review", "in_review"], limit)

    async def list_conflict(
        self, pk: str, limit: int = 50
    ) -> list[FormalizationTicket]:
        return await self._list_by_status(pk, ["conflict_pending"], limit)

    async def _list_by_status(
        self, pk: str, statuses: list[QueueStatus], limit: int
    ) -> list[FormalizationTicket]:
        placeholders = ",".join(f"@s{i}" for i in range(len(statuses)))
        params: list[dict[str, Any]] = [{"name": "@pk", "value": pk}]
        for i, s in enumerate(statuses):
            params.append({"name": f"@s{i}", "value": s})
        query = (
            f"SELECT TOP {int(limit)} * FROM c WHERE c.pk = @pk "
            f"AND c.status IN ({placeholders}) ORDER BY c.created_at ASC"
        )
        out: list[FormalizationTicket] = []
        async for it in self._c.query_items(
            query=query, parameters=params, partition_key=pk
        ):
            out.append(FormalizationTicket.model_validate(it))
        return out

    async def lock(
        self,
        ticket_id: str,
        pk: str,
        reviewer: str,
        ttl: int = _DEFAULT_LOCK_TTL_S,
    ) -> Optional[FormalizationTicket]:
        """Acquire a soft lock if no live lock exists. Returns the locked
        ticket on success, None on contention."""
        ticket = await self.get(ticket_id, pk)
        if ticket is None:
            return None
        now = datetime.now(timezone.utc)
        if (
            ticket.locked_by
            and ticket.lock_expires_at
            and ticket.lock_expires_at > now
            and ticket.locked_by != reviewer
        ):
            return None
        new_doc = ticket.model_dump(mode="json")
        new_doc["locked_by"] = reviewer
        new_doc["lock_expires_at"] = (now + timedelta(seconds=ttl)).isoformat()
        new_doc["status"] = "in_review"
        await self._c.upsert_item(new_doc)
        return FormalizationTicket.model_validate(new_doc)

    async def unlock(self, ticket_id: str, pk: str) -> None:
        ticket = await self.get(ticket_id, pk)
        if ticket is None:
            return
        doc = ticket.model_dump(mode="json")
        doc["locked_by"] = None
        doc["lock_expires_at"] = None
        if doc.get("status") == "in_review":
            doc["status"] = "pending_review"
        await self._c.upsert_item(doc)

    async def list_expired(
        self, pk: Optional[str] = None, limit: int = 100
    ) -> list[FormalizationTicket]:
        """Return tickets in `pending_review` or `in_review` whose `created_at`
        exceeds the 24h SLA. If `pk` is None, the caller must run this scan
        per-partition (Cosmos can't cross-partition without enable_xpartition).
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=_SLA_HOURS)
        params: list[dict[str, Any]] = [
            {"name": "@cutoff", "value": cutoff.isoformat()}
        ]
        query = (
            f"SELECT TOP {int(limit)} * FROM c WHERE c.status IN "
            "('pending_review', 'in_review') AND c.created_at < @cutoff"
        )
        kwargs: dict[str, Any] = {}
        if pk is not None:
            params.append({"name": "@pk", "value": pk})
            query = query.replace("WHERE c.status", "WHERE c.pk = @pk AND c.status")
            kwargs["partition_key"] = pk
        else:
            kwargs["enable_cross_partition_query"] = True

        out: list[FormalizationTicket] = []
        async for it in self._c.query_items(
            query=query, parameters=params, **kwargs
        ):
            out.append(FormalizationTicket.model_validate(it))
        return out
