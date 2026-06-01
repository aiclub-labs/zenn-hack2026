"""Schema Manager agent — implements ``SchemaManagerAgentI``.

Owns:
- revision_id auto-increment (load latest, +1)
- diff computation against previous revision
- audit log append (physical delete forbidden)
- ``schema.updated`` event emission via injected dispatcher
- cross-tenant bulk import (replace pk, reset revision_id=1)
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from app.contracts.agents import NotificationDispatcherI
from app.contracts.common import ChangeType, Tenant, make_pk, utcnow
from app.contracts.cosmos import SchemaAuditEntry, SchemaFieldDoc
from app.contracts.events import SchemaUpdatedEvent
from app.repos.schema_audit_log import SchemaAuditLogRepo
from app.repos.schemas import SchemasRepo

_DIFFABLE_FIELDS: tuple[str, ...] = (
    "field_name",
    "description",
    "expected_value_type",
    "example",
    "ai_baseline_assumption",
    "is_active",
)


def _history_url(sector: str, unit: str) -> str:
    return f"/admin/schemas/history?sector={sector}&unit={unit}"


def _diff(
    before: Optional[SchemaFieldDoc], after: SchemaFieldDoc
) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    if before is None:
        for f in _DIFFABLE_FIELDS:
            out[f] = {"before": None, "after": getattr(after, f)}
        return out
    for f in _DIFFABLE_FIELDS:
        b, a = getattr(before, f), getattr(after, f)
        if b != a:
            out[f] = {"before": b, "after": a}
    return out


def _summarize(diff: dict[str, dict[str, Any]]) -> str:
    if not diff:
        return "(no changes)"
    parts = [f"{k}: {v['before']!r}→{v['after']!r}" for k, v in diff.items()]
    return "; ".join(parts)


class SchemaManagerAgent:
    """Implements :class:`app.contracts.agents.SchemaManagerAgentI`."""

    def __init__(
        self,
        schemas: SchemasRepo,
        audit: SchemaAuditLogRepo,
        dispatcher: NotificationDispatcherI,
    ) -> None:
        self._schemas = schemas
        self._audit = audit
        self._dispatcher = dispatcher

    async def upsert(
        self, field: SchemaFieldDoc, reason: Optional[str] = None
    ) -> tuple[SchemaFieldDoc, SchemaAuditEntry]:
        prev = await self._schemas.get(field.id, field.pk)
        new_revision = (prev.revision_id + 1) if prev else 1
        change_type: ChangeType = "update" if prev else "create"

        next_doc = field.model_copy(
            update={"revision_id": new_revision, "updated_at": utcnow()}
        )
        await self._schemas.upsert(next_doc)

        diff = _diff(prev, next_doc)
        entry = SchemaAuditEntry(
            id=str(uuid.uuid4()),
            pk=next_doc.pk,
            schema_field_id=next_doc.id,
            revision_id=new_revision,
            change_type=change_type,
            diff=diff,
            reason=reason,
            changed_by=next_doc.updated_by,
            changed_at=next_doc.updated_at,
        )
        await self._audit.append(entry)

        await self._dispatcher.emit(
            SchemaUpdatedEvent(
                sector=next_doc.sector,
                unit=next_doc.unit,
                revision_id=new_revision,
                change_type=change_type,
                field_name=next_doc.field_name,
                diff_summary=_summarize(diff),
                history_url=_history_url(next_doc.sector, next_doc.unit),
                changed_by=next_doc.updated_by,
                changed_at=next_doc.updated_at,
            )
        )
        return next_doc, entry

    async def set_active(
        self,
        field_id: str,
        pk: str,
        is_active: bool,
        reason: Optional[str] = None,
    ) -> SchemaAuditEntry:
        prev = await self._schemas.get(field_id, pk)
        if prev is None:
            raise KeyError(f"schema not found: {field_id} / {pk}")
        if prev.is_active == is_active:
            # No-op, but we still record the intent for audit traceability.
            change_type: ChangeType = "reactivate" if is_active else "deactivate"
        else:
            change_type = "reactivate" if is_active else "deactivate"

        new_revision = prev.revision_id + 1
        now = utcnow()
        next_doc = prev.model_copy(
            update={
                "is_active": is_active,
                "revision_id": new_revision,
                "updated_at": now,
            }
        )
        await self._schemas.upsert(next_doc)

        diff = {"is_active": {"before": prev.is_active, "after": is_active}}
        entry = SchemaAuditEntry(
            id=str(uuid.uuid4()),
            pk=pk,
            schema_field_id=field_id,
            revision_id=new_revision,
            change_type=change_type,
            diff=diff,
            reason=reason,
            changed_by=next_doc.updated_by,
            changed_at=now,
        )
        await self._audit.append(entry)

        await self._dispatcher.emit(
            SchemaUpdatedEvent(
                sector=next_doc.sector,
                unit=next_doc.unit,
                revision_id=new_revision,
                change_type=change_type,
                field_name=next_doc.field_name,
                diff_summary=_summarize(diff),
                history_url=_history_url(next_doc.sector, next_doc.unit),
                changed_by=next_doc.updated_by,
                changed_at=now,
            )
        )
        return entry

    async def bulk_import(
        self, source: Tenant, target: Tenant
    ) -> list[SchemaFieldDoc]:
        src_pk = source.pk
        tgt_pk = target.pk
        actives = await self._schemas.list_active(src_pk)
        now = utcnow()
        imported: list[SchemaFieldDoc] = []
        for src in actives:
            # New id under the target tenant — never reuse the source id.
            new_id = f"{src.field_name}:{tgt_pk}"
            cloned = SchemaFieldDoc(
                id=new_id,
                pk=tgt_pk,
                sector=target.sector,
                unit=target.unit,
                field_name=src.field_name,
                description=src.description,
                expected_value_type=src.expected_value_type,
                example=src.example,
                ai_baseline_assumption=src.ai_baseline_assumption,
                is_active=True,
                revision_id=1,
                updated_at=now,
                updated_by=f"bulk_import:{source.sector}/{source.unit}",
            )
            await self._schemas.upsert(cloned)
            diff = _diff(None, cloned)
            await self._audit.append(
                SchemaAuditEntry(
                    id=str(uuid.uuid4()),
                    pk=tgt_pk,
                    schema_field_id=new_id,
                    revision_id=1,
                    change_type="create",
                    diff=diff,
                    reason=f"bulk_import from {source.sector}/{source.unit}",
                    changed_by=cloned.updated_by,
                    changed_at=now,
                )
            )
            imported.append(cloned)
        return imported

    async def get_history(
        self,
        tenant: Tenant,
        limit: int = 50,
        since: Optional[datetime] = None,
    ) -> list[SchemaAuditEntry]:
        return await self._audit.list(
            pk=make_pk(tenant.sector, tenant.unit),
            limit=limit,
            since=since,
        )
