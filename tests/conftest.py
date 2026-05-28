"""Shared pytest fixtures for dialogue-delta-formalization tests.

All fixtures are in-memory only — no Cosmos, no AI Search, no network.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock

# ---------------------------------------------------------------------------
# Prevent azure.cosmos from being imported at module level in repos that
# hard-import ContainerProxy. We stub out the azure.cosmos namespace so that
# importing app.repos.delta_events etc. works without the SDK installed in a
# pure-test environment.  The InMemoryContainer in _base.py is used instead.
# ---------------------------------------------------------------------------
for _mod in (
    "azure.cosmos",
    "azure.cosmos.aio",
    "azure.cosmos.exceptions",
    "azure.search.documents",
    "azure.search.documents.aio",
    "azure.search.documents.models",
    "azure.identity",
    "azure.identity.aio",
    "azure.keyvault.secrets",
    "azure.keyvault.secrets.aio",
    "azure.core.credentials",
):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()  # type: ignore[assignment]

import pytest

from app.contracts.common import Tenant
from app.repos._base import InMemoryContainer


@pytest.fixture
def tenant() -> Tenant:
    return Tenant(sector="sector_a", unit="unit_1")


@pytest.fixture
def pk(tenant: Tenant) -> str:
    return tenant.pk  # "sector_a#unit_1"


@pytest.fixture
def now() -> datetime:
    return datetime(2026, 5, 25, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def mem_container() -> InMemoryContainer:
    return InMemoryContainer()


@pytest.fixture
def second_mem_container() -> InMemoryContainer:
    return InMemoryContainer()
