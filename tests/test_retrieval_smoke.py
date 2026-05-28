"""Regression test for Issue #33 — guard against retrieval.py going back to stubs.

`_embed` / `_aisearch_query` shipped to prod as `[0.0]*8` / `[]` stubs and
self-critic ran without grounded citations. This smoke test pins the
contract by faking the embed + AI Search layers and asserting
``retrieve_for_turn`` actually composes citations / conflicts / prompt_ctx
from upstream hits.
"""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.api import retrieval as r
from app.contracts.common import Tenant


@pytest.mark.unit
@pytest.mark.asyncio
async def test_retrieve_for_turn_builds_citations_and_prompt_ctx(monkeypatch) -> None:
    monkeypatch.setattr(r, "_embed", AsyncMock(return_value=[0.1] * 1536))
    monkeypatch.setattr(
        r,
        "_aisearch_query",
        AsyncMock(
            return_value=[
                {
                    "record_id": "rec_1",
                    "schema_field_id": "sf_surface",
                    "weight": 0.8,
                    "superseded_by": None,
                    "content": "ライン A 表面処理: 焼付 170°C × 20 分",
                },
                {
                    "record_id": "rec_2",
                    "schema_field_id": "sf_surface",
                    "weight": 0.6,
                    "superseded_by": None,
                    "content": "ライン A 焼付 165°C ベスト",
                },
            ]
        ),
    )

    tenant = Tenant(sector="manufacturing-s8b", unit="line-A")
    citations, conflicts, prompt_ctx = await r.retrieve_for_turn(
        tenant=tenant, query="焼付温度はどう判断したか", user_id="u1"
    )

    assert [c.record_id for c in citations] == ["rec_1", "rec_2"]
    assert all(c.schema_field_id == "sf_surface" for c in citations)
    # >=2 distinct record_ids under one schema_field_id ⇒ conflict surfaced
    assert any(c["schema_field_id"] == "sf_surface" for c in conflicts)
    # prompt_ctx must carry actual snippets (not empty), keyed by record_id
    assert {p["citation_id"] for p in prompt_ctx} == {"rec_1", "rec_2"}
    assert all(p["snippet"] for p in prompt_ctx)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_retrieve_for_turn_no_hits_returns_empty(monkeypatch) -> None:
    monkeypatch.setattr(r, "_embed", AsyncMock(return_value=[0.0] * 1536))
    monkeypatch.setattr(r, "_aisearch_query", AsyncMock(return_value=[]))
    tenant = Tenant(sector="s", unit="u")
    citations, conflicts, prompt_ctx = await r.retrieve_for_turn(
        tenant=tenant, query="q", user_id="u"
    )
    assert citations == []
    assert conflicts == []
    assert prompt_ctx == []
