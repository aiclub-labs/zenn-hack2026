"""Provision the AI Search `corpus-{env}` index defined in contracts.md §3.

Bicep cannot create AI Search indexes — this script handles it.

Run after Bicep `aisearch.bicep` deploy:

    AISEARCH_ENDPOINT=https://srch-hack2026-...search.windows.net \
    AISEARCH_INDEX=corpus-dev \
    python scripts/provision_search_index.py

Auth: Managed Identity via DefaultAzureCredential (Cosmos disableLocalAuth=true
implies AAD-only access; same posture is applied to AI Search).
"""
from __future__ import annotations

import os
import sys

from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    HnswParameters,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)


def build_index(name: str) -> SearchIndex:
    """Build the index per contracts.md §3 (snake_case field names).

    `text-embedding-3-small` -> dim 1536.
    """
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SimpleField(name="sector", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="unit", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="pk", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="schema_field_id", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SearchField(
            name="atomic_claims",
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
            searchable=True,
        ),
        SimpleField(
            name="weight_final",
            type=SearchFieldDataType.Double,
            filterable=True,
            sortable=True,
        ),
        SimpleField(name="shareability", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="is_active", type=SearchFieldDataType.Boolean, filterable=True),
        SimpleField(name="superseded_by", type=SearchFieldDataType.String, filterable=True),
        SimpleField(
            name="created_at",
            type=SearchFieldDataType.DateTimeOffset,
            filterable=True,
            sortable=True,
        ),
        SearchField(
            name="vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536,
            vector_search_profile_name="hnsw-profile",
        ),
    ]
    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="hnsw-config",
                parameters=HnswParameters(m=4, ef_construction=400, ef_search=500, metric="cosine"),
            )
        ],
        profiles=[VectorSearchProfile(name="hnsw-profile", algorithm_configuration_name="hnsw-config")],
    )
    return SearchIndex(name=name, fields=fields, vector_search=vector_search)


def main() -> int:
    endpoint = os.environ.get("AISEARCH_ENDPOINT")
    index_name = os.environ.get("AISEARCH_INDEX", "corpus-dev")
    if not endpoint:
        print("ERR: AISEARCH_ENDPOINT not set", file=sys.stderr)
        return 1
    client = SearchIndexClient(endpoint=endpoint, credential=DefaultAzureCredential())
    index = build_index(index_name)
    existing = {i.name for i in client.list_indexes()}
    if index_name in existing:
        client.create_or_update_index(index)
        print(f"updated index: {index_name}")
    else:
        client.create_index(index)
        print(f"created index: {index_name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
