"""Azure OpenAI text-embedding-3-small wrapper.

Uses Managed Identity (DefaultAzureCredential) when running on Azure;
falls back to API key from env for local dev.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import cast

from openai import AsyncAzureOpenAI

_EMBED_DEPLOYMENT = os.getenv("AOAI_DEPLOYMENT_EMBED", "text-embedding-3-small")
_EMBED_DIM = 1536


@lru_cache(maxsize=1)
def _client() -> AsyncAzureOpenAI:
    endpoint = os.getenv("AOAI_ENDPOINT") or os.getenv("AZURE_OPENAI_ENDPOINT", "")
    api_key = os.getenv("AOAI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY", "")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
    if api_key:
        return AsyncAzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
        )
    # Managed Identity path
    from azure.identity.aio import DefaultAzureCredential, get_bearer_token_provider

    credential = DefaultAzureCredential()
    token_provider = get_bearer_token_provider(
        credential, "https://cognitiveservices.azure.com/.default"
    )
    return AsyncAzureOpenAI(
        azure_endpoint=endpoint,
        azure_ad_token_provider=token_provider,
        api_version=api_version,
    )


async def embed(text: str) -> list[float]:
    """Return a 1536-dim embedding for the given text."""
    if not text:
        return [0.0] * _EMBED_DIM
    client = _client()
    resp = await client.embeddings.create(model=_EMBED_DEPLOYMENT, input=text)
    return cast(list[float], list(resp.data[0].embedding))


def cosine_distance(a: list[float], b: list[float]) -> float:
    """Return cosine *distance* (1 - cosine similarity). Degenerate vectors → 1.0."""
    if not a or not b or len(a) != len(b):
        return 1.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na == 0.0 or nb == 0.0:
        return 1.0
    sim = dot / (na * nb)
    # Clamp because of float drift
    sim = max(-1.0, min(1.0, sim))
    return 1.0 - sim
