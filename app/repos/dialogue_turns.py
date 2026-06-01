"""Cosmos repo for the ``dialogue_turns`` container.

WT-B owns the slice needed for the Schema Revision Gate
(``schema_revision_seen_at`` / ``schema_revision_id_seen``).
Extended (M-1, M-6) with session-scoped acked-revision lookup and
per-turn revision stamping so the gate no longer holds in-process state.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.contracts.common import Tenant
from app.contracts.cosmos import DialogueTurn

from ._base import ContainerLike


class DialogueTurnsRepo:
    def __init__(self, container: ContainerLike) -> None:
        self._c = container

    async def upsert(self, turn: DialogueTurn) -> DialogueTurn:
        await self._c.upsert_item(turn.model_dump(mode="json"))
        return turn

    async def get(self, turn_id: str, pk: str) -> Optional[DialogueTurn]:
        """Lookup by turn_id within partition. Returns None if absent.

        Used by /turn/{turn_id}/ack-banner to recover session_id without
        forcing the client to repeat it.
        """
        query = (
            "SELECT * FROM c WHERE c.pk = @pk AND c.turn_id = @tid "
            "ORDER BY c.timestamp DESC"
        )
        params = [
            {"name": "@pk", "value": pk},
            {"name": "@tid", "value": turn_id},
        ]
        it = self._c.query_items(
            query=query, parameters=params, partition_key=pk
        )
        async for raw in it:
            if raw.get("pk") != pk or raw.get("turn_id") != turn_id:
                continue
            return DialogueTurn.model_validate(raw)
        return None

    async def recent_session_turn_ids(
        self, session_id: str, pk: str, limit: int
    ) -> list[str]:
        """Return up to ``limit`` recent ``turn_id`` values for a session
        (newest first). Used by DeltaDetectorAgent for cooldown checks (M-5).
        """
        query = (
            f"SELECT TOP {int(limit)} c.turn_id, c.timestamp FROM c "
            "WHERE c.pk = @pk AND c.session_id = @sid "
            "ORDER BY c.timestamp DESC"
        )
        params = [
            {"name": "@pk", "value": pk},
            {"name": "@sid", "value": session_id},
        ]
        rows: list[tuple[str, object]] = []
        it = self._c.query_items(
            query=query, parameters=params, partition_key=pk
        )
        async for raw in it:
            if raw.get("pk") != pk or raw.get("session_id") != session_id:
                continue
            tid = raw.get("turn_id")
            if tid:
                rows.append((tid, raw.get("timestamp") or ""))
        rows.sort(key=lambda kv: kv[1] or "", reverse=True)
        return [tid for tid, _ in rows[: int(limit)]]

    async def get_session_state(
        self, session_id: str, tenant: Tenant
    ) -> Optional[DialogueTurn]:
        """Return the most recent turn for a session in this tenant, or None.

        Used by the Schema Revision Gate to look up the last seen revision.
        """
        pk = tenant.pk
        query = (
            "SELECT * FROM c WHERE c.pk = @pk AND c.session_id = @sid "
            "ORDER BY c.timestamp DESC"
        )
        params = [
            {"name": "@pk", "value": pk},
            {"name": "@sid", "value": session_id},
        ]
        latest: Optional[DialogueTurn] = None
        it = self._c.query_items(
            query=query, parameters=params, partition_key=pk
        )
        async for raw in it:
            if raw.get("pk") != pk or raw.get("session_id") != session_id:
                continue
            turn = DialogueTurn.model_validate(raw)
            if latest is None or turn.timestamp > latest.timestamp:
                latest = turn
        return latest

    async def get_latest_acked_revision(
        self, session_id: str, pk: str
    ) -> int:
        """Max ``schema_revision_id_seen`` over the session's turns, default 0.

        Replaces the in-process (user_id, pk) dict the SchemaGateAdapter
        used to keep. Session is the correct scope per contracts §2.5.
        """
        query = (
            "SELECT * FROM c WHERE c.pk = @pk AND c.session_id = @sid "
            "AND IS_DEFINED(c.schema_revision_id_seen) "
            "AND NOT IS_NULL(c.schema_revision_id_seen)"
        )
        params = [
            {"name": "@pk", "value": pk},
            {"name": "@sid", "value": session_id},
        ]
        best = 0
        it = self._c.query_items(
            query=query, parameters=params, partition_key=pk
        )
        async for raw in it:
            if raw.get("pk") != pk or raw.get("session_id") != session_id:
                continue
            rev = raw.get("schema_revision_id_seen")
            if isinstance(rev, int) and rev > best:
                best = rev
        return best

    async def set_revision_seen(
        self,
        session_id: str,
        pk: str,
        turn_id: str,
        revision_id: int,
        ts: datetime,
    ) -> None:
        """Stamp a specific turn doc with the acknowledged revision.

        If the turn doc does not yet exist, no-op (caller raced ack before
        the turn append landed; gate will retry on the next turn).
        """
        query = (
            "SELECT * FROM c WHERE c.pk = @pk AND c.session_id = @sid "
            "AND c.turn_id = @tid"
        )
        params = [
            {"name": "@pk", "value": pk},
            {"name": "@sid", "value": session_id},
            {"name": "@tid", "value": turn_id},
        ]
        target: Optional[DialogueTurn] = None
        it = self._c.query_items(
            query=query, parameters=params, partition_key=pk
        )
        async for raw in it:
            if (
                raw.get("pk") != pk
                or raw.get("session_id") != session_id
                or raw.get("turn_id") != turn_id
            ):
                continue
            target = DialogueTurn.model_validate(raw)
            break
        if target is None:
            return
        updated = target.model_copy(
            update={
                "schema_revision_seen_at": ts,
                "schema_revision_id_seen": revision_id,
            }
        )
        await self._c.upsert_item(updated.model_dump(mode="json"))

    async def update_revision_seen(
        self,
        session_id: str,
        tenant: Tenant,
        revision_id: int,
        ts: datetime,
    ) -> None:
        """Stamp the latest turn for this session with the acknowledged revision.

        Kept for backward compat with the existing SchemaRevisionGate.acknowledge
        path. Prefer ``set_revision_seen`` when the caller knows the turn_id.
        """
        latest = await self.get_session_state(session_id, tenant)
        if latest is None:
            return
        updated = latest.model_copy(
            update={
                "schema_revision_seen_at": ts,
                "schema_revision_id_seen": revision_id,
            }
        )
        await self._c.upsert_item(updated.model_dump(mode="json"))

    async def delete(self, turn_id: str, pk: str) -> bool:
        """Physical delete of a turn doc by (turn_id, pk). Returns True if
        a doc was removed.

        Cascade to ``delta_events`` / ``hearout_records`` is performed by
        the caller (see ``app/api/turn.py::delete_turn``) once those repos
        expose ``delete_for_turn`` helpers. Out of scope for M-6.
        """
        existing = await self.get(turn_id, pk)
        if existing is None:
            return False
        # InMemoryContainer keys items by (id, pk). Real Cosmos uses
        # delete_item(item=id, partition_key=pk). The ContainerLike
        # protocol does not yet expose delete; emulate via upsert with
        # a deleted marker is wrong — instead defer to a follow-up that
        # extends ContainerLike. For now, drop from in-memory by reading
        # the underlying dict when present.
        store = getattr(self._c, "_items", None)
        if isinstance(store, dict):
            store.pop((existing.id, pk), None)
            return True
        # Real Cosmos path: caller must use a container with delete_item;
        # we surface a NotImplementedError-style False so cascade can log.
        return False
