"""Schema Revision Gate — compares session's last-seen revision against
the tenant's latest, emitting a banner until the user acknowledges.
"""
from __future__ import annotations

import logging
from typing import Optional

from app.contracts.common import Tenant, utcnow
from app.contracts.http import SchemaUpdateBanner
from app.repos.dialogue_turns import DialogueTurnsRepo
from app.repos.schemas import SchemasRepo
from app.util.telemetry import emit_metric

logger = logging.getLogger(__name__)

_METRIC_SHOWN = "schema.banner.shown"
_METRIC_ACKED = "schema.banner.acked"


class SchemaRevisionGate:
    """Determine whether a banner must be shown before invoking Delta Detector."""

    def __init__(
        self,
        schemas_repo: SchemasRepo,
        dialogue_turns_repo: DialogueTurnsRepo,
        history_url_template: str = "/schemas/history?sector={sector}&unit={unit}",
    ) -> None:
        self._schemas = schemas_repo
        self._turns = dialogue_turns_repo
        self._history_template = history_url_template

    async def check(
        self,
        session_id: str,
        tenant: Tenant,
        current_seen_revision: Optional[int],
    ) -> Optional[SchemaUpdateBanner]:
        """Return a SchemaUpdateBanner iff unseen revisions exist.

        ``current_seen_revision`` may be supplied by caller (cached) or
        looked up from the session's last turn when None.
        """
        pk = tenant.pk
        latest = await self._schemas.latest_revision_for_tenant(pk)
        if latest == 0:
            return None  # AllSeen (no schema yet)

        seen = current_seen_revision
        if seen is None:
            session_state = await self._turns.get_session_state(session_id, tenant)
            seen = (
                session_state.schema_revision_id_seen
                if session_state is not None
                else None
            )
        seen_value = seen or 0

        if seen_value >= latest:
            return None  # AllSeen

        unseen_fields = await self._schemas.list_unseen(pk, seen_value)
        if not unseen_fields:
            return None
        unseen_revisions = sorted({f.revision_id for f in unseen_fields})
        summary = ", ".join(
            f"{f.field_name} (rev {f.revision_id})" for f in unseen_fields[:5]
        )
        if len(unseen_fields) > 5:
            summary += f", +{len(unseen_fields) - 5} more"

        history_url = self._history_template.format(
            sector=tenant.sector, unit=tenant.unit
        )
        banner = SchemaUpdateBanner(
            unseen_revision_ids=unseen_revisions,
            changed_fields_summary=summary,
            history_url=history_url,
        )
        emit_metric(
            _METRIC_SHOWN,
            1.0,
            {
                "sector": tenant.sector,
                "unit": tenant.unit,
                "unseen_count": len(unseen_fields),
            },
        )
        return banner

    async def acknowledge(
        self, session_id: str, tenant: Tenant, revision_id: int
    ) -> None:
        """Stamp the session's most recent turn with the acknowledged revision."""
        await self._turns.update_revision_seen(
            session_id=session_id,
            tenant=tenant,
            revision_id=revision_id,
            ts=utcnow(),
        )
        emit_metric(
            _METRIC_ACKED,
            1.0,
            {
                "sector": tenant.sector,
                "unit": tenant.unit,
                "revision_id": revision_id,
            },
        )
