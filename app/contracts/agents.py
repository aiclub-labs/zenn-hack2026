"""Agent interface protocols. MAF 1.0 Python SDK implementations conform to these."""
from datetime import datetime
from typing import Optional, Protocol

from pydantic import BaseModel, ConfigDict

from .common import (
    ConflictDecision,
    HearoutStatus,
    ReviewDecision,
    Tenant,
    TJVerdict,
)
from .cosmos import (
    DeltaEvent,
    DialogueTurn,
    FormalizationTicket,
    HearoutRecord,
    SchemaAuditEntry,
    SchemaFieldDoc,
    TruthJudgmentLog,
)
from .events import NotificationEvent


class HearoutTurn(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    session_id: str
    status: HearoutStatus
    next_question: Optional[str] = None
    final_record: Optional[HearoutRecord] = None
    turn_count: int


class CorpusUpsertResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    record_id: str
    corpus_meta_id: str


class ConflictResolution(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    ticket_id: str
    decision: ConflictDecision
    affected_record_ids: list[str]


class SchemaManagerAgentI(Protocol):
    async def upsert(
        self, field: SchemaFieldDoc, reason: Optional[str] = None
    ) -> tuple[SchemaFieldDoc, SchemaAuditEntry]: ...
    async def set_active(
        self, field_id: str, pk: str, is_active: bool, reason: Optional[str] = None
    ) -> SchemaAuditEntry: ...
    async def bulk_import(
        self, source: Tenant, target: Tenant
    ) -> list[SchemaFieldDoc]: ...
    async def get_history(
        self, tenant: Tenant, limit: int = 50, since: Optional[datetime] = None
    ) -> list[SchemaAuditEntry]: ...


class DeltaDetectorAgentI(Protocol):
    async def detect(self, turn: DialogueTurn) -> list[DeltaEvent]: ...


class HearoutAgentI(Protocol):
    async def start(
        self, gap_event_id: str, user_id: str, tenant: Tenant
    ) -> HearoutTurn: ...
    async def respond(self, session_id: str, answer: str) -> HearoutTurn: ...
    async def skip(self, session_id: str) -> HearoutRecord: ...


class FormalizationAgentI(Protocol):
    async def weight(
        self, record: HearoutRecord
    ) -> tuple[float, float, float, float]: ...
    async def submit_for_review(
        self,
        record: HearoutRecord,
        weights: tuple[float, float, float, float],
        tj_verdict: Optional[TJVerdict],
    ) -> FormalizationTicket: ...
    async def on_review_decision(
        self,
        ticket_id: str,
        pk: str,
        decision: ReviewDecision,
        edited: Optional[HearoutRecord] = None,
    ) -> CorpusUpsertResult: ...
    async def on_conflict_decision(
        self, ticket_id: str, pk: str, decision: ConflictDecision
    ) -> ConflictResolution: ...


class TruthJudgmentI(Protocol):
    async def judge(self, record: HearoutRecord) -> TruthJudgmentLog: ...


class NotificationDispatcherI(Protocol):
    async def emit(self, event: NotificationEvent) -> None: ...
