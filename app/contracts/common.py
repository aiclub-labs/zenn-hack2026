"""Common types shared across all agents/APIs. Source of truth for partition keys & enums."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

PK = str  # f"{sector}#{unit}"


class Tenant(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    sector: str
    unit: str

    @property
    def pk(self) -> PK:
        return f"{self.sector}#{self.unit}"


ExpectedValueType = Literal["string", "number", "enum", "structured"]
Shareability = Literal["private", "unit", "public"]
ChangeType = Literal["create", "update", "deactivate", "reactivate"]
ReviewDecision = Literal["approve", "edit", "reject"]
ConflictDecision = Literal["adopt_new", "keep_existing", "coexist"]
TJVerdict = Literal["supported", "novel", "conflict"]
QueueStatus = Literal[
    "pending_review", "in_review", "approved", "rejected", "expired", "conflict_pending"
]
HearoutOutcome = Literal["completed", "skipped", "expired"]
HearoutStatus = Literal["in_progress", "completed", "skipped", "expired"]
DeltaPattern = Literal["input-time", "activation-time"]
Role = Literal["user", "assistant"]


def make_pk(sector: str, unit: str) -> PK:
    return f"{sector}#{unit}"


def utcnow() -> datetime:
    from datetime import timezone
    return datetime.now(timezone.utc)
