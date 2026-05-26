"""Notification Dispatcher.

Implements ``NotificationDispatcherI``. Maps event type -> Discord webhook
URL (KV-managed), applies PII scrubbing, retries with exponential backoff,
falls back to admin webhook + error_logs on terminal failure.

KV secret names per contracts.md §7:
- DISCORD_WEBHOOK_URL_SCHEMA_UPDATES
- DISCORD_WEBHOOK_URL_PENDING_REVIEW
- DISCORD_WEBHOOK_URL_EXPIRED
- DISCORD_WEBHOOK_URL_COST_ALERT
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

import httpx
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.contracts.common import utcnow
from app.contracts.cosmos import ErrorLog
from app.contracts.events import NotificationEvent
from app.util import pii
from app.util.kv import KeyVaultClient
from app.util.telemetry import emit_metric

from .discord import to_discord_payload

logger = logging.getLogger(__name__)

_KV_SECRET_BY_EVENT_TYPE: dict[str, str] = {
    "schema.updated": "DISCORD-WEBHOOK-URL-SCHEMA-UPDATES",
    "record.pending_review": "DISCORD-WEBHOOK-URL-PENDING-REVIEW",
    "record.expired": "DISCORD-WEBHOOK-URL-EXPIRED",
    "cost.alert.fired": "DISCORD-WEBHOOK-URL-COST-ALERT",
}

# Admin / operator fallback channel (same KV as cost alerts by default).
_ADMIN_FALLBACK_SECRET = "DISCORD-WEBHOOK-URL-COST-ALERT"

_METRIC_DISPATCHED = "schema.notify.dispatched"


class NotificationDispatcher:
    """Conforms to ``NotificationDispatcherI`` protocol."""

    def __init__(
        self,
        kv: Optional[KeyVaultClient] = None,
        http_client: Optional[httpx.AsyncClient] = None,
        error_logs_repo: Any = None,  # TODO(WT-D): tighten once ErrorLogsRepo wired in DI
        admin_pk: str = "ops#default",
    ) -> None:
        self._kv = kv
        self._http = http_client
        self._error_logs = error_logs_repo
        self._admin_pk = admin_pk

    def _kv_client(self) -> KeyVaultClient:
        if self._kv is None:
            self._kv = KeyVaultClient.instance()
        return self._kv

    def _http_client(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=10.0)
        return self._http

    async def emit(self, event: NotificationEvent) -> None:
        # 1. Map event -> KV secret
        secret_name = _KV_SECRET_BY_EVENT_TYPE.get(event.event_type)
        if secret_name is None:
            logger.error("No webhook mapping for event_type=%s", event.event_type)
            emit_metric(
                _METRIC_DISPATCHED,
                1.0,
                {"event_type": event.event_type, "success": False},
            )
            return

        # 2. Build payload + PII scrub (Req 16.6)
        raw_payload = to_discord_payload(event)
        scrubbed = pii.scrub(raw_payload)

        success = False
        last_exc: Optional[BaseException] = None
        try:
            webhook_url = await self._kv_client().get_secret(secret_name)
            await self._post_with_retry(webhook_url, scrubbed)
            success = True
        except (RetryError, httpx.HTTPError, Exception) as exc:  # noqa: BLE001
            last_exc = exc
            logger.exception(
                "Notification dispatch failed event_type=%s", event.event_type
            )

        emit_metric(
            _METRIC_DISPATCHED,
            1.0,
            {"event_type": event.event_type, "success": success},
        )

        if success:
            return

        # 5. Final failure: log to error_logs + admin fallback webhook
        await self._record_failure(event, scrubbed, last_exc)

    async def _post_with_retry(
        self, webhook_url: str, payload: dict[str, Any]
    ) -> None:
        client = self._http_client()
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=4.0),
            retry=retry_if_exception_type((httpx.HTTPError,)),
            reraise=True,
        ):
            with attempt:
                resp = await client.post(webhook_url, json=payload)
                # Discord returns 204 on success; treat 4xx/5xx as retryable.
                if resp.status_code >= 400:
                    raise httpx.HTTPStatusError(
                        f"Discord webhook returned {resp.status_code}",
                        request=resp.request,
                        response=resp,
                    )

    async def _record_failure(
        self,
        event: NotificationEvent,
        scrubbed_payload: dict[str, Any],
        exc: Optional[BaseException],
    ) -> None:
        # TODO(WT-D): wire ErrorLog repo via DI; until then accept None gracefully.
        entry = ErrorLog(
            id=str(uuid.uuid4()),
            pk=self._admin_pk,
            ts=utcnow(),
            agent="notification_dispatcher",
            stack=repr(exc) if exc is not None else "unknown",
            last_turn_meta={
                "event_type": event.event_type,
                # Payload is already PII-scrubbed; safe to keep for triage.
                "payload_summary": scrubbed_payload.get("embeds", [{}])[0].get(
                    "description", ""
                ),
            },
        )
        if self._error_logs is not None:
            try:
                await self._error_logs.append(entry)
            except Exception:  # pragma: no cover - degraded mode
                logger.exception("error_logs append failed")

        # Admin fallback webhook
        try:
            admin_url = await self._kv_client().get_secret(_ADMIN_FALLBACK_SECRET)
            fallback_payload = {
                "content": (
                    f":warning: dispatch failure for `{event.event_type}` — "
                    f"see error_logs id={entry.id}"
                ),
            }
            await self._http_client().post(admin_url, json=fallback_payload)
        except Exception:  # pragma: no cover - last-resort path
            logger.exception("Admin fallback webhook also failed")
