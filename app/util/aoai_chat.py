"""Shared AsyncAzureOpenAI chat client.

Prefers API key when set, falls back to Managed Identity bearer token.
"""
from __future__ import annotations

from functools import lru_cache

from openai import AsyncAzureOpenAI

from app.config import settings


@lru_cache(maxsize=1)
def chat_client() -> AsyncAzureOpenAI:
    if settings.azure_openai_api_key:
        return AsyncAzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
        )
    from azure.identity.aio import DefaultAzureCredential, get_bearer_token_provider

    credential = DefaultAzureCredential()
    token_provider = get_bearer_token_provider(
        credential, "https://cognitiveservices.azure.com/.default"
    )
    return AsyncAzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        azure_ad_token_provider=token_provider,
        api_version=settings.azure_openai_api_version,
    )


def deployment_small() -> str:
    name = settings.azure_openai_deployment_small
    if not name:
        raise RuntimeError(
            "azure_openai_deployment_small unset — refuse silent fallback (Issue #42)"
        )
    return name


def deployment_large() -> str:
    name = settings.azure_openai_deployment_large
    if not name:
        raise RuntimeError(
            "azure_openai_deployment_large unset — refuse silent fallback (Issue #42)"
        )
    return name


__all__ = ["chat_client", "deployment_small", "deployment_large"]
