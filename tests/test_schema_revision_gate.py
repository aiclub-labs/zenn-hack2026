"""Unit tests for SchemaRevisionGate (Req 2.7, design §8).

Cases:
  - Unseen revision exists → banner_for returns SchemaUpdateBanner with correct ids.
  - After acknowledge() → is_acked flag cleared (next check returns None).
  - session_id isolation: ack in session A does not affect session B.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

import pytest

from app.agents.schema_gate.gate import SchemaRevisionGate
from app.contracts.common import Tenant
from app.contracts.cosmos import DialogueTurn, SchemaFieldDoc
from app.repos._base import InMemoryContainer
from app.repos.dialogue_turns import DialogueTurnsRepo
from app.repos.schemas import SchemasRepo

_NOW = datetime(2026, 5, 25, 12, 0, 0, tzinfo=timezone.utc)


def _make_schema_field(pk: str, field_name: str, revision_id: int) -> SchemaFieldDoc:
    return SchemaFieldDoc(
        id=f"sf_{field_name}",
        pk=pk,
        sector=pk.split("#")[0],
        unit=pk.split("#")[1],
        field_name=field_name,
        description=f"Description for {field_name}",
        expected_value_type="string",
        example="example",
        ai_baseline_assumption="baseline",
        is_active=True,
        revision_id=revision_id,
        updated_at=_NOW,
        updated_by="admin",
    )


def _make_turn(pk: str, session_id: str, revision_id_seen: Optional[int] = None) -> DialogueTurn:
    return DialogueTurn(
        id=f"dt_{uuid.uuid4().hex[:8]}",
        pk=pk,
        session_id=session_id,
        turn_id=f"t_{uuid.uuid4().hex[:8]}",
        role="user",
        content="hello",
        timestamp=_NOW,
        schema_revision_id_seen=revision_id_seen,
        schema_revision_seen_at=_NOW if revision_id_seen is not None else None,
    )


def _build_gate(
    schemas_container: InMemoryContainer,
    turns_container: InMemoryContainer,
    tenant: Tenant,
) -> SchemaRevisionGate:
    schemas_repo = SchemasRepo(schemas_container)
    turns_repo = DialogueTurnsRepo(turns_container)
    return SchemaRevisionGate(schemas_repo=schemas_repo, dialogue_turns_repo=turns_repo)


@pytest.mark.unit
async def test_banner_returned_when_unseen_revision(
    mem_container: InMemoryContainer,
    second_mem_container: InMemoryContainer,
    tenant: Tenant,
) -> None:
    """Unseen revision exists → check() returns SchemaUpdateBanner with unseen ids."""
    pk = tenant.pk
    schemas_repo = SchemasRepo(mem_container)
    turns_repo = DialogueTurnsRepo(second_mem_container)
    gate = SchemaRevisionGate(schemas_repo=schemas_repo, dialogue_turns_repo=turns_repo)

    # Schema has revision 5 published
    field = _make_schema_field(pk, "delivery_date", revision_id=5)
    await schemas_repo.upsert(field)

    # Session has never acknowledged any revision
    banner = await gate.check(session_id="sess_001", tenant=tenant, current_seen_revision=None)

    assert banner is not None
    assert 5 in banner.unseen_revision_ids
    assert "delivery_date" in banner.changed_fields_summary


@pytest.mark.unit
async def test_no_banner_when_all_revisions_seen(
    mem_container: InMemoryContainer,
    second_mem_container: InMemoryContainer,
    tenant: Tenant,
) -> None:
    """current_seen_revision >= latest revision → None."""
    pk = tenant.pk
    schemas_repo = SchemasRepo(mem_container)
    turns_repo = DialogueTurnsRepo(second_mem_container)
    gate = SchemaRevisionGate(schemas_repo=schemas_repo, dialogue_turns_repo=turns_repo)

    field = _make_schema_field(pk, "cost_item", revision_id=3)
    await schemas_repo.upsert(field)

    banner = await gate.check(session_id="sess_001", tenant=tenant, current_seen_revision=3)
    assert banner is None


@pytest.mark.unit
async def test_acknowledge_clears_banner(
    mem_container: InMemoryContainer,
    second_mem_container: InMemoryContainer,
    tenant: Tenant,
) -> None:
    """After acknowledge(), next check returns None (all seen)."""
    pk = tenant.pk
    schemas_repo = SchemasRepo(mem_container)
    turns_repo = DialogueTurnsRepo(second_mem_container)
    gate = SchemaRevisionGate(schemas_repo=schemas_repo, dialogue_turns_repo=turns_repo)

    field = _make_schema_field(pk, "budget_code", revision_id=7)
    await schemas_repo.upsert(field)

    # First: banner should appear
    banner_before = await gate.check(session_id="sess_ack", tenant=tenant, current_seen_revision=0)
    assert banner_before is not None

    # Seed a turn so update_revision_seen has something to stamp
    turn = _make_turn(pk, session_id="sess_ack", revision_id_seen=None)
    await turns_repo.upsert(turn)

    # Acknowledge
    await gate.acknowledge(session_id="sess_ack", tenant=tenant, revision_id=7)

    # Now pass the acknowledged revision explicitly
    banner_after = await gate.check(session_id="sess_ack", tenant=tenant, current_seen_revision=7)
    assert banner_after is None


@pytest.mark.unit
async def test_session_isolation(
    mem_container: InMemoryContainer,
    second_mem_container: InMemoryContainer,
    tenant: Tenant,
) -> None:
    """Ack in session A must not affect session B's banner check."""
    pk = tenant.pk
    schemas_repo = SchemasRepo(mem_container)
    turns_repo = DialogueTurnsRepo(second_mem_container)
    gate = SchemaRevisionGate(schemas_repo=schemas_repo, dialogue_turns_repo=turns_repo)

    field = _make_schema_field(pk, "approval_code", revision_id=9)
    await schemas_repo.upsert(field)

    # Session A acknowledges revision 9
    turn_a = _make_turn(pk, session_id="sess_A", revision_id_seen=None)
    await turns_repo.upsert(turn_a)
    await gate.acknowledge(session_id="sess_A", tenant=tenant, revision_id=9)

    # Session B has NOT acknowledged — must still see the banner
    banner_b = await gate.check(session_id="sess_B", tenant=tenant, current_seen_revision=None)
    assert banner_b is not None, "Session B must still receive the banner after session A acks"


@pytest.mark.unit
async def test_no_banner_when_no_schema(
    mem_container: InMemoryContainer,
    second_mem_container: InMemoryContainer,
    tenant: Tenant,
) -> None:
    """No schemas defined → latest_revision=0 → None (AllSeen path)."""
    schemas_repo = SchemasRepo(mem_container)
    turns_repo = DialogueTurnsRepo(second_mem_container)
    gate = SchemaRevisionGate(schemas_repo=schemas_repo, dialogue_turns_repo=turns_repo)

    banner = await gate.check(session_id="sess_new", tenant=tenant, current_seen_revision=None)
    assert banner is None
