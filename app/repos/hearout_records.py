"""Cosmos repo for `hearout_records` (Req 5).

Records evolve incrementally during a 5W1H session. Status persisted as a
top-level `status` field for resume; final outcome stored on the contract
`outcome` field once the session terminates.
"""
from __future__ import annotations

from typing import Any, Optional

from azure.cosmos.aio import ContainerProxy
from azure.cosmos.exceptions import CosmosResourceNotFoundError

from app.contracts.cosmos import HearoutRecord


class HearoutRecordsRepo:
    container_name = "hearout_records"

    def __init__(self, container: ContainerProxy) -> None:
        self._c = container

    async def upsert(
        self,
        record: HearoutRecord,
        extra_state: Optional[dict[str, Any]] = None,
    ) -> HearoutRecord:
        """Upsert the record. `extra_state` is merged into the persisted doc
        (e.g. live `status`, next_question) but is not part of the frozen
        contract — it is dropped on read via `HearoutRecord.model_validate`."""
        doc: dict[str, Any] = record.model_dump(mode="json")
        if extra_state:
            doc.update(extra_state)
        await self._c.upsert_item(doc)
        return record

    async def get(self, record_id: str, pk: str) -> Optional[HearoutRecord]:
        try:
            doc = await self._c.read_item(item=record_id, partition_key=pk)
        except CosmosResourceNotFoundError:
            return None
        # Strip non-contract keys before validation (extra="forbid")
        allowed = set(HearoutRecord.model_fields.keys())
        clean = {k: v for k, v in doc.items() if k in allowed}
        return HearoutRecord.model_validate(clean)

    async def get_raw(self, record_id: str, pk: str) -> Optional[dict[str, Any]]:
        """Return the full underlying doc (includes live session state)."""
        try:
            doc = await self._c.read_item(item=record_id, partition_key=pk)
            return dict(doc)
        except CosmosResourceNotFoundError:
            return None

    async def get_by_session(
        self, session_id: str, pk: str
    ) -> Optional[dict[str, Any]]:
        """Return the most-recent raw doc whose record_id == ``session_id``
        (HearoutAgent surfaces record_id as the public session id).

        Multi-replica safe: source of truth is Cosmos, not process memory.
        Returns the underlying doc (incl. extra session state) so the agent
        can rehydrate ``HearoutSessionState``. ``pk`` MUST be provided —
        contracts §1 forbids cross-partition scans on hot path.
        """
        # record_id is the doc id; pk = tenant partition key.
        try:
            doc = await self._c.read_item(item=session_id, partition_key=pk)
            return dict(doc)
        except CosmosResourceNotFoundError:
            return None

    async def list_by_session(
        self, pk: str, session_id: str, limit: int = 20
    ) -> list[HearoutRecord]:
        query = (
            f"SELECT TOP {int(limit)} * FROM c WHERE c.pk = @pk "
            "AND c.session_id = @sid ORDER BY c._ts DESC"
        )
        params = [
            {"name": "@pk", "value": pk},
            {"name": "@sid", "value": session_id},
        ]
        out: list[HearoutRecord] = []
        allowed = set(HearoutRecord.model_fields.keys())
        async for it in self._c.query_items(
            query=query, parameters=params, partition_key=pk
        ):
            clean = {k: v for k, v in it.items() if k in allowed}
            out.append(HearoutRecord.model_validate(clean))
        return out
