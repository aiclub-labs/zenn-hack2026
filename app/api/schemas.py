"""Schema CRUD endpoints (Persona A / 知識管理者).

Requirements covered:
- Req 1 (POST), Req 2 (PATCH, active toggle, history Req 2.6), Req 3 (bulk import)

Auth: ``require_admin_role`` is a header-based stub today. Real Entra ID OIDC
integration lands tomorrow; the dependency is structured so swapping it does
not change handler signatures.
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from app.agents.schema_manager import SchemaManagerAgent
from app.api._deps import get_schemas_repo
from app.contracts.common import Tenant, make_pk, utcnow
from app.contracts.cosmos import SchemaAuditEntry, SchemaFieldDoc
from app.contracts.http import BulkImportRequest, SetActiveRequest
from app.repos.schemas import SchemasRepo

router = APIRouter(prefix="/schemas", tags=["schemas"])


# --- auth stub -------------------------------------------------------------


async def require_admin_role(
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(default=None, alias="X-User-Role"),
) -> str:
    """Stub Entra ID admin check.

    TODO(WT-A): swap for OIDC token validation + ``app_role`` claim check.
    """
    if os.getenv("DEV_SKIP_AUTH", "").lower() == "true":
        return x_user_id or "dev-admin"
    if x_user_role != "schema_admin":
        raise HTTPException(status_code=403, detail="schema_admin role required")
    if not x_user_id:
        raise HTTPException(status_code=401, detail="X-User-Id missing")
    return x_user_id


# --- DI wiring (overridden by app/main.py once WT-B containers land) -------


_agent_instance: Optional[SchemaManagerAgent] = None


def set_agent(agent: SchemaManagerAgent) -> None:
    global _agent_instance
    _agent_instance = agent


def get_agent() -> SchemaManagerAgent:
    if _agent_instance is None:
        raise HTTPException(
            status_code=503,
            detail="SchemaManagerAgent not wired; override get_agent in app startup",
        )
    return _agent_instance


# --- request bodies --------------------------------------------------------


class SchemaUpsertBody(SchemaFieldDoc):
    """Reuses the doc shape; client supplies all required fields.

    ``revision_id`` and ``updated_at`` on the request are ignored — the agent
    auto-increments and stamps them server-side.
    """


# M-8: SetActiveBody is retained as a thin alias of the contract type so the
# router signature stays stable. The canonical model lives in
# ``app.contracts.http.SetActiveRequest``.
SetActiveBody = SetActiveRequest


# --- routes ----------------------------------------------------------------


@router.post("", response_model=SchemaFieldDoc)
async def create_schema(
    body: SchemaUpsertBody,
    user_id: str = Depends(require_admin_role),
    agent: SchemaManagerAgent = Depends(get_agent),
) -> SchemaFieldDoc:
    # Server stamps updated_by + revision; client values are overridden.
    incoming = body.model_copy(
        update={
            "updated_by": user_id,
            "updated_at": utcnow(),
            "revision_id": 1,
        }
    )
    doc, _ = await agent.upsert(incoming, reason=None)
    return doc


@router.patch("/{field_id}", response_model=SchemaFieldDoc)
async def update_schema(
    field_id: str,
    body: SchemaUpsertBody,
    user_id: str = Depends(require_admin_role),
    agent: SchemaManagerAgent = Depends(get_agent),
) -> SchemaFieldDoc:
    if body.id != field_id:
        raise HTTPException(status_code=400, detail="body.id != path id")
    incoming = body.model_copy(
        update={"updated_by": user_id, "updated_at": utcnow()}
    )
    doc, _ = await agent.upsert(incoming, reason=None)
    return doc


@router.post("/{field_id}/active", response_model=SchemaAuditEntry)
async def toggle_active(
    field_id: str,
    body: SetActiveBody,
    pk: str = Query(..., description="partition key sector#unit"),
    user_id: str = Depends(require_admin_role),
    agent: SchemaManagerAgent = Depends(get_agent),
) -> SchemaAuditEntry:
    try:
        return await agent.set_active(
            field_id=field_id, pk=pk, is_active=body.is_active, reason=body.reason
        )
    except KeyError as exc:  # noqa: BLE001
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/bulk-import", response_model=list[SchemaFieldDoc])
async def bulk_import(
    body: BulkImportRequest,
    user_id: str = Depends(require_admin_role),
    agent: SchemaManagerAgent = Depends(get_agent),
) -> list[SchemaFieldDoc]:
    src = Tenant(sector=body.source_sector, unit=body.source_unit)
    tgt = Tenant(sector=body.target_sector, unit=body.target_unit)
    return await agent.bulk_import(src, tgt)


@router.get("/history", response_model=list[SchemaAuditEntry])
async def get_history(
    sector: str = Query(...),
    unit: str = Query(...),
    limit: int = Query(50, ge=1, le=500),
    since: Optional[datetime] = Query(default=None),
    user_id: str = Depends(require_admin_role),
    agent: SchemaManagerAgent = Depends(get_agent),
) -> list[SchemaAuditEntry]:
    tenant = Tenant(sector=sector, unit=unit)
    _ = make_pk(sector, unit)  # validation only
    return await agent.get_history(tenant=tenant, limit=limit, since=since)


@router.get("/history/public", response_model=list[SchemaAuditEntry])
async def get_history_public(
    sector: str = Query(...),
    unit: str = Query(...),
    limit: int = Query(50, ge=1, le=500),
    since: Optional[datetime] = Query(default=None),
    agent: SchemaManagerAgent = Depends(get_agent),
) -> list[SchemaAuditEntry]:
    """Req 2 AC6 / Issue #31: business-user-facing read-only changelog.

    Same data as ``/history`` but no admin role gate. ``changed_by`` is masked
    to a generic ``"reviewer"`` token so reviewer identity is not leaked to
    業務ユーザー (Persona B/C).
    """
    tenant = Tenant(sector=sector, unit=unit)
    _ = make_pk(sector, unit)
    entries = await agent.get_history(tenant=tenant, limit=limit, since=since)
    return [e.model_copy(update={"changed_by": "reviewer"}) for e in entries]


@router.get("", response_model=list[SchemaFieldDoc])
async def list_schemas(
    sector: str = Query(...),
    unit: str = Query(...),
    active_only: bool = Query(True),
    user_id: str = Depends(require_admin_role),
    repo: SchemasRepo = Depends(get_schemas_repo),
) -> list[SchemaFieldDoc]:
    """M-7: list current schemas for a tenant.

    Replaces the Admin UI's prior history-replay derivation; reads the
    container directly (O(N) on tenant pk only).
    """
    pk = make_pk(sector, unit)
    return await repo.list(pk=pk, active_only=active_only)


__all__: list[Any] = ["router", "require_admin_role", "get_agent"]
