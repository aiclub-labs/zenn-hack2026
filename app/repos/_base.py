"""Minimal Cosmos container protocol + in-memory fallback for local dev / tests.

WT-B will provide the real ``azure.cosmos.aio.ContainerProxy``-backed client.
Until then, repos accept any object implementing :class:`ContainerLike` so
WT-C code paths can be exercised offline.
"""
from __future__ import annotations

from typing import Any, AsyncIterator, Optional, Protocol


class ContainerLike(Protocol):
    async def upsert_item(self, body: dict[str, Any]) -> dict[str, Any]: ...
    async def read_item(self, item: str, partition_key: str) -> dict[str, Any]: ...
    def query_items(
        self,
        query: str,
        parameters: Optional[list[dict[str, Any]]] = None,
        partition_key: Optional[str] = None,
        enable_cross_partition_query: bool = False,
    ) -> AsyncIterator[dict[str, Any]]: ...


class InMemoryContainer:
    """Lightweight in-memory fallback. Not thread-safe; demo-grade."""

    def __init__(self) -> None:
        self._items: dict[tuple[str, str], dict[str, Any]] = {}

    async def upsert_item(self, body: dict[str, Any]) -> dict[str, Any]:
        key = (body["id"], body["pk"])
        self._items[key] = dict(body)
        return dict(body)

    async def read_item(self, item: str, partition_key: str) -> dict[str, Any]:
        return dict(self._items[(item, partition_key)])

    async def _iter(self) -> AsyncIterator[dict[str, Any]]:
        for v in list(self._items.values()):
            yield dict(v)

    def query_items(
        self,
        query: str,
        parameters: Optional[list[dict[str, Any]]] = None,
        partition_key: Optional[str] = None,
        enable_cross_partition_query: bool = False,
    ) -> AsyncIterator[dict[str, Any]]:
        # Tests/dev should filter in Python after iterating.
        return self._iter()
