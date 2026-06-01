"""Shared FastAPI dependencies for WT-E routers.

These are thin import-stable accessors. The concrete implementations are
owned by WT-B (repos, schema-gate, notification), WT-C (schema repos),
and WT-D (agents, embedding, AI Search). Until their modules land we fall
back to in-memory containers / no-op stubs so the routers stay importable
and locally exercisable.
"""
from __future__ import annotations

from typing import Any, Optional, Protocol

from fastapi import Request

from app.contracts.agents import (
    ConflictResolution,
    CorpusUpsertResult,
    FormalizationAgentI,
    HearoutAgentI,
    HearoutTurn,
)
from app.contracts.common import (
    ConflictDecision,
    ReviewDecision,
    Tenant,
)
from app.contracts.cosmos import HearoutRecord as HearoutRecordDoc
from app.contracts.http import SchemaUpdateBanner


class SchemaRevisionGateI(Protocol):
    async def banner_for(
        self, user_id: str, tenant: Tenant, session_id: str
    ) -> Optional[SchemaUpdateBanner]: ...

    async def acknowledge(
        self,
        user_id: str,
        tenant: Tenant,
        session_id: str,
        turn_id: str,
    ) -> None: ...

    async def is_acked(
        self, user_id: str, tenant: Tenant, session_id: str
    ) -> bool: ...


class _NoopSchemaGate:
    async def banner_for(
        self, user_id: str, tenant: Tenant, session_id: str
    ) -> Optional[SchemaUpdateBanner]:
        return None

    async def acknowledge(
        self,
        user_id: str,
        tenant: Tenant,
        session_id: str,
        turn_id: str,
    ) -> None:
        return None

    async def is_acked(
        self, user_id: str, tenant: Tenant, session_id: str
    ) -> bool:
        return True


class DialogueTurnsRepoI(Protocol):
    async def upsert(self, turn: Any) -> Any: ...
    async def get(self, turn_id: str, pk: str) -> Any: ...
    async def get_latest_acked_revision(
        self, session_id: str, pk: str
    ) -> int: ...
    async def set_revision_seen(
        self,
        session_id: str,
        pk: str,
        turn_id: str,
        revision_id: int,
        ts: Any,
    ) -> None: ...
    async def delete(self, turn_id: str, pk: str) -> bool: ...


class _StubDialogueTurnsRepo:
    async def upsert(self, turn: Any) -> Any:
        return turn

    async def get(self, turn_id: str, pk: str) -> Any:
        return None

    async def get_latest_acked_revision(
        self, session_id: str, pk: str
    ) -> int:
        return 0

    async def set_revision_seen(
        self,
        session_id: str,
        pk: str,
        turn_id: str,
        revision_id: int,
        ts: Any,
    ) -> None:
        return None

    async def delete(self, turn_id: str, pk: str) -> bool:
        return False


class _StubHearoutAgent:
    async def start(
        self, gap_event_id: str, user_id: str, tenant: Tenant
    ) -> HearoutTurn:
        raise RuntimeError("HearoutAgent not wired yet (WT-D)")

    async def respond(self, session_id: str, answer: str) -> HearoutTurn:
        raise RuntimeError("HearoutAgent not wired yet (WT-D)")

    async def skip(self, session_id: str) -> HearoutRecordDoc:  # type: ignore[override]
        raise RuntimeError("HearoutAgent not wired yet (WT-D)")


class _StubFormalizationAgent:
    async def weight(
        self, record: HearoutRecordDoc
    ) -> tuple[float, float, float, float]:
        raise RuntimeError("FormalizationAgent not wired yet (WT-D)")

    async def submit_for_review(
        self,
        record: HearoutRecordDoc,
        weights: tuple[float, float, float, float],
        tj_verdict: Optional[str],
    ) -> Any:
        raise RuntimeError("FormalizationAgent not wired yet (WT-D)")

    async def on_review_decision(
        self,
        ticket_id: str,
        pk: str,
        decision: ReviewDecision,
        edited: Optional[HearoutRecordDoc] = None,
    ) -> CorpusUpsertResult:
        raise RuntimeError("FormalizationAgent not wired yet (WT-D)")

    async def on_conflict_decision(
        self, ticket_id: str, pk: str, decision: ConflictDecision
    ) -> ConflictResolution:
        raise RuntimeError("FormalizationAgent not wired yet (WT-D)")


# --- Singletons (replaced by app.main wiring once WT-B/C/D land) ---

_schema_gate: SchemaRevisionGateI = _NoopSchemaGate()
_hearout_agent: HearoutAgentI = _StubHearoutAgent()  # type: ignore[assignment]
_formalization_agent: FormalizationAgentI = _StubFormalizationAgent()  # type: ignore[assignment]
_dialogue_turns_repo: DialogueTurnsRepoI = _StubDialogueTurnsRepo()


def get_schema_gate() -> SchemaRevisionGateI:
    return _schema_gate


def get_hearout_agent() -> HearoutAgentI:
    return _hearout_agent


def get_formalization_agent() -> FormalizationAgentI:
    return _formalization_agent


def get_dialogue_turns_repo() -> DialogueTurnsRepoI:
    return _dialogue_turns_repo


def set_schema_gate(gate: SchemaRevisionGateI) -> None:
    global _schema_gate
    _schema_gate = gate


def set_hearout_agent(agent: HearoutAgentI) -> None:
    global _hearout_agent
    _hearout_agent = agent


def set_formalization_agent(agent: FormalizationAgentI) -> None:
    global _formalization_agent
    _formalization_agent = agent


def set_dialogue_turns_repo(repo: DialogueTurnsRepoI) -> None:
    global _dialogue_turns_repo
    _dialogue_turns_repo = repo


def current_reviewer_scope(request: Request) -> list[Tenant]:
    from app.util.auth import parse_easy_auth_headers

    _, scope = parse_easy_auth_headers(request)
    return scope


def current_reviewer_id(request: Request) -> str:
    from app.util.auth import parse_easy_auth_headers

    reviewer_id, _ = parse_easy_auth_headers(request)
    return reviewer_id


# --- SchemasRepo accessor (M-7) ----------------------------------------------

_schemas_repo: Any = None


def get_schemas_repo() -> Any:
    if _schemas_repo is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=503,
            detail="SchemasRepo not wired; build_and_register() must run first",
        )
    return _schemas_repo


def set_schemas_repo(repo: Any) -> None:
    global _schemas_repo
    _schemas_repo = repo


# --- DeltaDetectorAgent accessor (M-5) ---------------------------------------
#
# turn.py invokes the detector as fire-and-forget. When unwired (local boot
# without Azure SDKs) the accessor returns None and turn.py simply logs.

_delta_detector: Any = None


def get_delta_detector() -> Any:
    return _delta_detector


def set_delta_detector(detector: Any) -> None:
    global _delta_detector
    _delta_detector = detector


# --- FormalizationQueueRepo accessor (wt-b-import) ---------------------------

_formalization_queue_repo: Any = None


def get_formalization_queue_repo() -> Any:
    return _formalization_queue_repo


def set_formalization_queue_repo(repo: Any) -> None:
    global _formalization_queue_repo
    _formalization_queue_repo = repo
