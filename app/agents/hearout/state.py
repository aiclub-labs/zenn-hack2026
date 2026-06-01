"""Hearout in-progress session state (persisted alongside hearout_records)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from app.contracts.common import HearoutStatus


@dataclass
class HearoutSessionState:
    """Mutable session-scoped state for an in-flight hearout interview.

    Persisted as extra keys on the `hearout_records` doc; stripped on read by
    the repo before returning the frozen `HearoutRecord` contract.
    """

    record_id: str
    pk: str
    gap_event_id: str
    session_id: str
    user_id: str
    status: HearoutStatus = "in_progress"
    turn_count: int = 0
    transcript: list[dict[str, str]] = field(default_factory=list)
    slots: dict[str, Optional[str]] = field(default_factory=dict)
    next_question: Optional[str] = None
    self_critic: float = 0.0

    def to_extra(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "user_id": self.user_id,
            "next_question": self.next_question,
            "session_self_critic": self.self_critic,
        }
