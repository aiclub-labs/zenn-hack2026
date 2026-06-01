"""Cosmos container client factory.

Uses ``DefaultAzureCredential`` (Container App system-assigned MI) when the
account endpoint is set. Caller is responsible for keeping the returned
``CosmosClient`` alive for the app lifetime.
"""
from __future__ import annotations

import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

_client = None
_database = None


def get_database():  # type: ignore[no-untyped-def]
    """Return the dialogue_delta database client, or None if unconfigured."""
    global _client, _database
    if _database is not None:
        return _database
    endpoint = settings.cosmos_endpoint
    if not endpoint:
        return None
    try:
        from azure.cosmos.aio import CosmosClient
        from azure.identity.aio import DefaultAzureCredential

        credential = DefaultAzureCredential()
        _client = CosmosClient(endpoint, credential=credential)
        _database = _client.get_database_client(settings.cosmos_database)
        logger.info(
            "cosmos.connected endpoint=%s database=%s",
            endpoint,
            settings.cosmos_database,
        )
        return _database
    except Exception as exc:  # pragma: no cover
        logger.warning("cosmos.connect_failed: %s", exc)
        return None


def get_container(name: str):  # type: ignore[no-untyped-def]
    """Return container client by name, or None."""
    db = get_database()
    if db is None:
        return None
    try:
        return db.get_container_client(name)
    except Exception as exc:  # pragma: no cover
        logger.warning("cosmos.get_container_failed name=%s: %s", name, exc)
        return None


__all__ = ["get_database", "get_container"]
