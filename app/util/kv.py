"""Key Vault client wrapper with TTL-cached secret fetch.

Uses Managed Identity via DefaultAzureCredential. KV URI from KEY_VAULT_URI env.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Optional

from azure.identity.aio import DefaultAzureCredential
from azure.keyvault.secrets.aio import SecretClient


@dataclass
class _CacheEntry:
    value: str
    expires_at: float


class KeyVaultClient:
    """Singleton-style async KV client with per-secret TTL cache."""

    _instance: Optional["KeyVaultClient"] = None

    def __init__(self, vault_uri: Optional[str] = None, ttl_seconds: int = 300) -> None:
        uri = vault_uri or os.environ.get("KEY_VAULT_URI", "")
        if not uri:
            raise RuntimeError("KEY_VAULT_URI not set and no vault_uri provided")
        self._vault_uri = uri
        self._ttl = ttl_seconds
        self._cache: dict[str, _CacheEntry] = {}
        self._credential = DefaultAzureCredential()
        self._client = SecretClient(vault_url=uri, credential=self._credential)

    @classmethod
    def instance(cls) -> "KeyVaultClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def get_secret(self, name: str) -> str:
        now = time.monotonic()
        cached = self._cache.get(name)
        if cached is not None and cached.expires_at > now:
            return cached.value
        secret = await self._client.get_secret(name)
        value = secret.value or ""
        self._cache[name] = _CacheEntry(value=value, expires_at=now + self._ttl)
        return value

    async def close(self) -> None:
        await self._client.close()
        await self._credential.close()
