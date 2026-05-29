"""Cosmos DB document shapes (12 collections). All partition_key = '/pk'."""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

from .common import (
    ChangeType,
    ConflictDecision,
    DeltaPattern,
    ExpectedValueType,
    HearoutOutcome,
    QueueStatus,
    ReviewDecision,
    Role,
    Shareability,
    TJVerdict,
)


class _DocBase(BaseModel):
    # ignore (not forbid) so Cosmos-injected system fields (_rid, _self,
    # _etag, _attachments, _ts) round-trip cleanly through model_validate.
    model_config = ConfigDict(extra="ignore", frozen=True)


class SchemaFieldDoc(_DocBase):
    id: str
    pk: str
    sector: str
    unit: str
    field_name: str
    description: str
    expected_value_type: ExpectedValueType
    example: str
    ai_baseline_assumption: str
    is_active: bool = True
    revision_id: int
    updated_at: datetime
    updated_by: str


class SchemaAuditEntry(_DocBase):
    id: str
    pk: str
    schema_field_id: str
    revision_id: int
    change_type: ChangeType
    diff: dict[str, dict[str, Any]]
    reason: Optional[str] = None
    changed_by: str
    changed_at: datetime


class SchemaCandidate(_DocBase):
    id: str
    pk: str
    turn_id: str
    suggested_field_hint: str
    llm_reason: str
    occurrences: int
    last_seen_at: datetime


class PromptTemplate(_DocBase):
    id: str
    pk: str
    terminology: dict[str, str]
    industry_examples: list[str]
    scenario_prompts: dict[str, str]


class DialogueTurn(_DocBase):
    id: str
    pk: str
    session_id: str
    turn_id: str
    role: Role
    content: Optional[str] = None  # None when redact=True
    self_critic_score: Optional[float] = None  # 0-10
    self_critic_reason: Optional[str] = None
    redact: bool = False
    timestamp: datetime
    schema_revision_seen_at: Optional[datetime] = None
    schema_revision_id_seen: Optional[int] = None
    # P2-C1: retrieval ↔ generation 層分離。assistant turn にのみ載る。
    # citation_ids: top-k citation_id (生成入力に渡したもの)
    # top_k_scores: 並列 list (citation_ids と同 index, AI Search score)
    # query_hash: 質問文の SHA-256 prefix (PII 漏えい回避のためハッシュのみ)
    retrieval_ctx: Optional[dict] = None


class DeltaEvent(_DocBase):
    id: str
    pk: str
    turn_id: str
    schema_field_id: Optional[str] = None  # None = out-of-schema
    self_critic: float
    distance: float
    gap_detected: bool
    cooldown_until: Optional[datetime] = None
    matched_reason: str


class HearoutRecord(_DocBase):
    id: str
    pk: str
    gap_event_id: str
    session_id: str
    transcript: list[dict[str, str]]
    who: Optional[str] = None
    what: Optional[str] = None
    when: Optional[str] = None
    where: Optional[str] = None
    why: Optional[str] = None
    how: Optional[str] = None
    outcome: HearoutOutcome
    turn_count: int


class FormalizationTicket(_DocBase):
    id: str
    pk: str
    hearout_id: str
    weight_a: float
    weight_b: float = 1.0
    weight_c: float = 1.0
    weight_final: float
    tj_verdict: Optional[TJVerdict] = None
    status: QueueStatus
    locked_by: Optional[str] = None
    lock_expires_at: Optional[datetime] = None
    reviewer_id: Optional[str] = None
    decision: Optional[ReviewDecision] = None
    conflict_decision: Optional[ConflictDecision] = None
    edit_diff: Optional[dict[str, Any]] = None
    expired_at: Optional[datetime] = None
    created_at: datetime


class TruthJudgmentLog(_DocBase):
    id: str
    pk: str
    record_id: str
    atomic_claims: list[str]
    evidence_score: float
    ensemble_votes: list[dict[str, Any]]
    verdict: TJVerdict
    pattern: DeltaPattern


class CorpusMeta(_DocBase):
    id: str
    pk: str
    record_id: str
    schema_field_id: str
    referenced_count: int = 0
    last_referenced_at: Optional[datetime] = None
    shareability: Shareability = "private"
    is_active: bool = True
    superseded_by: Optional[str] = None
    coexisting_views: Optional[list[str]] = None


class CitationAuditEntry(_DocBase):
    id: str
    pk: str
    old_record_id: str
    new_record_id: str
    transition: str  # "superseded" | "coexists"
    occurred_at: datetime


class ErrorLog(_DocBase):
    id: str
    pk: str
    ts: datetime
    agent: str
    stack: str
    last_turn_meta: dict[str, Any]  # never contains turn.content


COLLECTIONS: tuple[str, ...] = (
    "schemas",
    "schema_audit_log",
    "schema_candidate_log",
    "prompt_templates",
    "dialogue_turns",
    "delta_events",
    "hearout_records",
    "formalization_queue",
    "truth_judgment_logs",
    "corpus_meta",
    "citation_audit_log",
    "error_logs",
)
