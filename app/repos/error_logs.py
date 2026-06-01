"""Cosmos repo for the ``error_logs`` container (append-only).

Used by the Notification Dispatcher on terminal webhook failure (Req 16.4).
``last_turn_meta`` MUST NEVER contain raw turn content (Req 7 / 17.4).
"""
from __future__ import annotations

from app.contracts.cosmos import ErrorLog

from ._base import ContainerLike


class ErrorLogsRepo:
    def __init__(self, container: ContainerLike) -> None:
        self._c = container

    async def append(self, entry: ErrorLog) -> ErrorLog:
        await self._c.upsert_item(entry.model_dump(mode="json"))
        return entry
