"""HTTP request/response shapes for FastAPI endpoints."""
from typing import Optional

from pydantic import BaseModel, ConfigDict


class _HTTPBase(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class CitationRef(_HTTPBase):
    record_id: str
    schema_field_id: str
    weight: float
    superseded_by: Optional[str] = None


class SchemaUpdateBanner(_HTTPBase):
    unseen_revision_ids: list[int]
    changed_fields_summary: str
    history_url: str


class TurnRequest(_HTTPBase):
    user_id: str
    sector: str
    unit: str
    session_id: str
    user_content: str
    redact: bool = False


class TurnResponse(_HTTPBase):
    turn_id: str
    ai_response: str
    self_critic_score: float
    # KPMG Explainability / Issue #38: surface judge rationale to Chat UI.
    # Tooltip shown when score < 5 (low-confidence answers).
    self_critic_reason: Optional[str] = None
    citations: list[CitationRef]
    schema_update_banner: Optional[SchemaUpdateBanner] = None
    gap_detected: bool
    # First DeltaEvent.id of the burst (if any). UI uses this to call
    # POST /hearout/start so HearoutAgent can resolve the originating
    # gap. None when gap_detected is False.
    gap_event_id: Optional[str] = None


class HearoutStartRequest(_HTTPBase):
    gap_event_id: str
    user_id: str
    sector: str
    unit: str


class RetrieveResponse(_HTTPBase):
    records: list[CitationRef]
    conflicts: list[dict]  # [{schema_field_id, alt_count}]


class HearoutRespondRequest(_HTTPBase):
    answer: str  # use literal "SKIP" to skip


class ReviewDecisionRequest(_HTTPBase):
    decision: str  # ReviewDecision
    edited_record: Optional[dict] = None


class ConflictDecisionRequest(_HTTPBase):
    decision: str  # ConflictDecision


class SetActiveRequest(_HTTPBase):
    """Body for ``POST /schemas/{id}/active`` (M-8).

    The partition key is supplied via the ``?pk=`` query string; only the
    activation toggle + optional reason flow through the body.
    """

    is_active: bool
    reason: Optional[str] = None


class BulkImportRequest(_HTTPBase):
    source_sector: str
    source_unit: str
    target_sector: str
    target_unit: str


class CitationDetail(_HTTPBase):
    record_id: str
    content: str
    schema_field_id: str
    superseded_by: Optional[str] = None
    superseded_banner: Optional[str] = None
