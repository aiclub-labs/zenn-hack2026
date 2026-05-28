"""Event payloads for Notification Dispatcher and internal pub/sub."""
from datetime import datetime
from typing import Literal, Union

from pydantic import BaseModel, ConfigDict


class _EventBase(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SchemaUpdatedEvent(_EventBase):
    event_type: Literal["schema.updated"] = "schema.updated"
    sector: str
    unit: str
    revision_id: int
    change_type: str
    field_name: str
    diff_summary: str
    history_url: str
    changed_by: str
    changed_at: datetime


class PendingReviewEvent(_EventBase):
    event_type: Literal["record.pending_review"] = "record.pending_review"
    ticket_id: str
    sector: str
    unit: str
    user_id: str
    weight_final: float
    reason: str


class ExpiredEvent(_EventBase):
    event_type: Literal["record.expired"] = "record.expired"
    ticket_id: str
    sector: str
    unit: str
    reviewer_id: str
    user_id: str
    expired_at: datetime


class CostAlertEvent(_EventBase):
    event_type: Literal["cost.alert.fired"] = "cost.alert.fired"
    threshold_usd: float
    cumulative_usd: float
    period_start: datetime
    period_end: datetime


NotificationEvent = Union[
    SchemaUpdatedEvent, PendingReviewEvent, ExpiredEvent, CostAlertEvent
]
