"""Pure function: NotificationEvent -> Discord webhook JSON payload.

Color coding per design.md §4.6 hotspot:
- gray   (0x95A5A6): schema.updated
- yellow (0xF1C40F): record.pending_review
- orange (0xE67E22): record.expired
- red    (0xE74C3C): cost.alert.fired
"""
from __future__ import annotations

from typing import Any

from app.contracts.events import (
    CostAlertEvent,
    ExpiredEvent,
    NotificationEvent,
    PendingReviewEvent,
    SchemaUpdatedEvent,
)

_COLOR_BY_TYPE: dict[str, int] = {
    "schema.updated": 0x95A5A6,
    "record.pending_review": 0xF1C40F,
    "record.expired": 0xE67E22,
    "cost.alert.fired": 0xE74C3C,
}


def _fields_from_event(event: NotificationEvent) -> list[dict[str, Any]]:
    raw = event.model_dump(mode="json")
    fields: list[dict[str, Any]] = []
    for key, value in raw.items():
        if key == "event_type":
            continue
        fields.append(
            {"name": key, "value": str(value)[:1024] or "-", "inline": True}
        )
    return fields


def to_discord_payload(event: NotificationEvent) -> dict[str, Any]:
    color = _COLOR_BY_TYPE.get(event.event_type, 0x7289DA)
    title = event.event_type
    if isinstance(event, SchemaUpdatedEvent):
        description = f"{event.change_type}: `{event.field_name}` (rev {event.revision_id})"
    elif isinstance(event, PendingReviewEvent):
        description = f"Pending review ticket `{event.ticket_id}` (weight={event.weight_final:.2f})"
    elif isinstance(event, ExpiredEvent):
        description = f"Ticket `{event.ticket_id}` expired at {event.expired_at.isoformat()}"
    elif isinstance(event, CostAlertEvent):
        description = (
            f"Cumulative ${event.cumulative_usd:.2f} crossed "
            f"threshold ${event.threshold_usd:.2f}"
        )
    else:  # pragma: no cover - exhaustive over Union
        description = title
    embed: dict[str, Any] = {
        "title": title,
        "description": description,
        "color": color,
        "fields": _fields_from_event(event),
    }
    return {"embeds": [embed]}
