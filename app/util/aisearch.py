"""AI Search Basic wrapper around the `corpus-{env}` index.

Hybrid (vector + filter) query with shareability / is_active / supersededBy filters.
Auth: Managed Identity only (Req 17.1 — API キー直接利用禁止 / Issue #40).
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Optional

from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizedQuery

from app.contracts.common import Shareability, Tenant

_INDEX_NAME = os.getenv("AISEARCH_INDEX", f"corpus-{os.getenv('ENV', 'dev')}")
_ENDPOINT = os.getenv("AISEARCH_ENDPOINT", "")

_SHAREABILITY_RANK: dict[str, int] = {"private": 0, "unit": 1, "public": 2}


def _credential() -> Any:
    from azure.identity.aio import DefaultAzureCredential

    return DefaultAzureCredential()


@lru_cache(maxsize=1)
def _client() -> SearchClient:
    return SearchClient(
        endpoint=_ENDPOINT,
        index_name=_INDEX_NAME,
        credential=_credential(),
    )


class CorpusIndex:
    """Wrapper exposing only the operations the agents need."""

    def __init__(self, client: Optional[SearchClient] = None) -> None:
        self._client = client or _client()

    async def upsert(self, record: dict[str, Any]) -> None:
        """Upsert a corpus document. Must already contain `vector`."""
        # Azure SDK uses merge_or_upload via `upload_documents` w/ key replacement
        await self._client.merge_or_upload_documents(documents=[record])

    async def query(
        self,
        tenant: Tenant,
        query_vec: list[float],
        top_k: int = 10,
        filter_active: bool = True,
        exclude_superseded: bool = True,
        shareability_min: Shareability = "private",
    ) -> list[dict[str, Any]]:
        """Hybrid vector query with partition + visibility filters."""
        filters: list[str] = [
            f"sector eq '{tenant.sector}'",
            f"unit eq '{tenant.unit}'",
        ]
        if filter_active:
            filters.append("is_active eq true")
        if exclude_superseded:
            filters.append("(superseded_by eq null or superseded_by eq '')")

        min_rank = _SHAREABILITY_RANK.get(shareability_min, 0)
        allowed = [k for k, v in _SHAREABILITY_RANK.items() if v >= min_rank]
        if allowed:
            allowed_clause = " or ".join(f"shareability eq '{s}'" for s in allowed)
            filters.append(f"({allowed_clause})")

        vector_query = VectorizedQuery(
            vector=query_vec, k_nearest_neighbors=top_k, fields="vector"
        )
        results = await self._client.search(
            search_text=None,
            vector_queries=[vector_query],
            filter=" and ".join(filters),
            top=top_k,
        )
        out: list[dict[str, Any]] = []
        async for doc in results:
            out.append(dict(doc))
        return out
