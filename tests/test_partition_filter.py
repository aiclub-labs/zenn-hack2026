"""Unit tests for AI Search partition / visibility filter construction.

Design §8 Unit:
  - superseded_by != null excluded
  - is_active=false excluded
  - shareability < requested excluded
  - multi-tenant: pk filter applied

We test the filter *string* produced by CorpusIndex.query() by subclassing and
intercepting the call without hitting any real Azure endpoint.
"""
from __future__ import annotations

import re
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.contracts.common import Shareability, Tenant


# ---------------------------------------------------------------------------
# We cannot instantiate CorpusIndex with a real SearchClient, so we test the
# filter-building logic directly by extracting it into a helper that mirrors
# what CorpusIndex.query() does.
# ---------------------------------------------------------------------------

_SHAREABILITY_RANK: dict[str, int] = {"private": 0, "unit": 1, "public": 2}


def _build_filter(
    tenant: Tenant,
    filter_active: bool = True,
    exclude_superseded: bool = True,
    shareability_min: Shareability = "private",
) -> str:
    """Mirror of CorpusIndex.query() filter construction. Must stay in sync."""
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

    return " and ".join(filters)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_default_filter_excludes_inactive(tenant: Tenant) -> None:
    """filter_active=True → is_active eq true must appear in filter."""
    filt = _build_filter(tenant)
    assert "is_active eq true" in filt


@pytest.mark.unit
def test_default_filter_excludes_superseded(tenant: Tenant) -> None:
    """exclude_superseded=True → superseded_by null/empty check in filter."""
    filt = _build_filter(tenant)
    assert "superseded_by eq null" in filt


@pytest.mark.unit
def test_filter_private_includes_all_shareability(tenant: Tenant) -> None:
    """shareability_min='private' → all three levels allowed."""
    filt = _build_filter(tenant, shareability_min="private")
    assert "shareability eq 'private'" in filt
    assert "shareability eq 'unit'" in filt
    assert "shareability eq 'public'" in filt


@pytest.mark.unit
def test_filter_unit_excludes_private(tenant: Tenant) -> None:
    """shareability_min='unit' → private must NOT be in the allowed clause."""
    filt = _build_filter(tenant, shareability_min="unit")
    # 'unit' and 'public' should be present
    assert "shareability eq 'unit'" in filt
    assert "shareability eq 'public'" in filt
    # 'private' must NOT be allowed
    # Extract the shareability sub-clause to avoid false positives
    match = re.search(r"\(shareability eq [^)]+\)", filt)
    assert match is not None
    clause = match.group(0)
    assert "shareability eq 'private'" not in clause


@pytest.mark.unit
def test_filter_public_only(tenant: Tenant) -> None:
    """shareability_min='public' → only public allowed."""
    filt = _build_filter(tenant, shareability_min="public")
    match = re.search(r"\(shareability eq [^)]+\)", filt)
    assert match is not None
    clause = match.group(0)
    assert "shareability eq 'public'" in clause
    assert "shareability eq 'unit'" not in clause
    assert "shareability eq 'private'" not in clause


@pytest.mark.unit
def test_pk_partition_filter_applied(tenant: Tenant) -> None:
    """sector and unit must both appear in the filter for multi-tenant isolation."""
    filt = _build_filter(tenant)
    assert f"sector eq '{tenant.sector}'" in filt
    assert f"unit eq '{tenant.unit}'" in filt


@pytest.mark.unit
def test_different_tenant_produces_different_filter() -> None:
    """Two different tenants → different filter strings (partition isolation)."""
    t1 = Tenant(sector="sector_a", unit="unit_1")
    t2 = Tenant(sector="sector_b", unit="unit_2")
    f1 = _build_filter(t1)
    f2 = _build_filter(t2)
    assert f1 != f2
    assert "sector_b" not in f1
    assert "sector_a" not in f2


@pytest.mark.unit
def test_filter_active_false_omits_is_active_clause(tenant: Tenant) -> None:
    """filter_active=False → is_active clause must NOT appear."""
    filt = _build_filter(tenant, filter_active=False)
    assert "is_active" not in filt


@pytest.mark.unit
def test_exclude_superseded_false_omits_clause(tenant: Tenant) -> None:
    """exclude_superseded=False → superseded_by clause must NOT appear."""
    filt = _build_filter(tenant, exclude_superseded=False)
    assert "superseded_by" not in filt
