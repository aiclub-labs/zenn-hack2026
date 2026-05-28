"""Easy Auth header parsing (Container Apps / App Service auth).

Container Apps Easy Auth surfaces the validated principal to the upstream
container via two headers:

* ``X-MS-CLIENT-PRINCIPAL-NAME`` — the user's UPN (string).
* ``X-MS-CLIENT-PRINCIPAL``      — base64-encoded JSON describing the user,
  including ``claims`` (a list of ``{typ, val}`` records). The Entra ID
  group object IDs arrive as claims with ``typ == "groups"``.

This helper decodes those headers and maps each group claim through an
operator-configured ``REVIEWER_GROUP_TENANT_MAP`` (env var holding JSON
of the form ``{"<group-object-id>": ["sector#unit", ...]}``) into a list
of :class:`Tenant` scopes — exactly the shape ``reviews.py`` consumes via
``current_reviewer_scope``.

Local-dev fallback: if the headers are absent and ``settings.environment``
indicates dev/local, the helper returns the synthetic
``("local-dev-reviewer", [])`` tuple so the API stays exercisable without
the Easy Auth front-end.
"""
from __future__ import annotations

import base64
import binascii
import json
import logging
from typing import Optional

from fastapi import Request

from app.config import settings
from app.contracts.common import Tenant

logger = logging.getLogger(__name__)

_DEV_ENVS = frozenset({"dev", "local", "development"})
_HDR_NAME = "X-MS-CLIENT-PRINCIPAL-NAME"
_HDR_PRINCIPAL = "X-MS-CLIENT-PRINCIPAL"
# Issue #35: dev-only override so reviewers can be switched from the UI to
# exercise the fairness pivot. Honored ONLY when settings.environment is dev/local.
_HDR_REVIEWER_OVERRIDE = "X-Reviewer-Id"


def _parse_pk(pk: str) -> Optional[Tenant]:
    sector, sep, unit = pk.partition("#")
    if not sep or not sector or not unit:
        return None
    return Tenant(sector=sector, unit=unit)


def _decode_groups(b64_principal: str) -> list[str]:
    """Return the list of group object IDs from the base64 principal blob."""
    try:
        raw = base64.b64decode(b64_principal, validate=False)
        payload = json.loads(raw.decode("utf-8"))
    except (binascii.Error, ValueError, UnicodeDecodeError) as exc:
        logger.warning("Easy Auth principal decode failed: %s", exc)
        return []

    groups: list[str] = []
    claims = payload.get("claims") if isinstance(payload, dict) else None
    if isinstance(claims, list):
        for c in claims:
            if not isinstance(c, dict):
                continue
            if c.get("typ") == "groups" and isinstance(c.get("val"), str):
                groups.append(c["val"])
    # Some Easy Auth shapes flatten groups under a top-level key.
    top = payload.get("groups") if isinstance(payload, dict) else None
    if isinstance(top, list):
        groups.extend(str(g) for g in top if isinstance(g, (str, int)))
    return groups


def _scopes_for_groups(groups: list[str]) -> list[Tenant]:
    mapping = getattr(settings, "reviewer_group_tenant_map", None) or {}
    if not isinstance(mapping, dict):
        return []
    seen: set[str] = set()
    out: list[Tenant] = []
    for g in groups:
        pks = mapping.get(g)
        if not isinstance(pks, list):
            continue
        for pk in pks:
            if not isinstance(pk, str) or pk in seen:
                continue
            seen.add(pk)
            tenant = _parse_pk(pk)
            if tenant is not None:
                out.append(tenant)
    return out


def parse_easy_auth_headers(request: Request) -> tuple[str, list[Tenant]]:
    """Resolve ``(reviewer_id, allowed_scope)`` from a FastAPI request.

    Falls back to ``("local-dev-reviewer", [])`` when both headers are
    missing AND the configured environment is a dev/local one.
    """
    name = request.headers.get(_HDR_NAME)
    principal_b64 = request.headers.get(_HDR_PRINCIPAL)
    env = (settings.environment or "").lower()

    # Dev-only header override (Issue #35). In prod we ignore X-Reviewer-Id
    # entirely so a downstream attacker cannot spoof a reviewer by adding
    # the header — Easy Auth is the source of truth.
    if env in _DEV_ENVS:
        override = request.headers.get(_HDR_REVIEWER_OVERRIDE)
        if override:
            return (override.strip(), [])

    if not name and not principal_b64:
        if env in _DEV_ENVS:
            return ("local-dev-reviewer", [])
        # In prod the absence of Easy Auth headers is suspicious but not
        # actionable from this helper — surface an anonymous identity and
        # let the downstream handler decide whether to 401.
        return ("anonymous", [])

    reviewer_id = name or "anonymous"
    groups = _decode_groups(principal_b64) if principal_b64 else []
    return (reviewer_id, _scopes_for_groups(groups))


__all__ = ["parse_easy_auth_headers"]
