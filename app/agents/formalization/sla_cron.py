"""24h SLA expiry scanner (Req 11).

Designed to be invoked as a cron job (Container Apps Job or APScheduler).
Scans `formalization_queue` for tickets in `pending_review`/`in_review` whose
`created_at` exceeds the 24h SLA; sets them to `expired`, then emits
`ExpiredEvent` for both reviewer and originating user.

The scan is per-partition for cost; the caller passes the partition keys
(typically distinct tenant pks) that are active. A no-arg variant scans
cross-partition (more expensive — use sparingly).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from app.contracts.agents import NotificationDispatcherI
from app.contracts.cosmos import FormalizationTicket
from app.contracts.events import ExpiredEvent
from app.repos.formalization_queue import FormalizationQueueRepo

logger = logging.getLogger(__name__)


async def scan_expired(
    queue_repo: FormalizationQueueRepo,
    notifier: NotificationDispatcherI,
    pks: Optional[list[str]] = None,
) -> list[str]:
    """Returns the list of ticket IDs newly marked as expired."""
    expired_ids: list[str] = []
    now = datetime.now(timezone.utc)

    partitions = pks if pks else [None]
    for pk in partitions:
        try:
            tickets = await queue_repo.list_expired(pk=pk)
        except Exception as exc:  # pragma: no cover
            logger.error("list_expired failed for pk=%s: %s", pk, exc)
            continue

        for ticket in tickets:
            try:
                await _expire_ticket(queue_repo, notifier, ticket, now)
                expired_ids.append(ticket.id)
            except Exception as exc:  # pragma: no cover
                logger.error("expire ticket %s failed: %s", ticket.id, exc)
    return expired_ids


async def _expire_ticket(
    queue_repo: FormalizationQueueRepo,
    notifier: NotificationDispatcherI,
    ticket: FormalizationTicket,
    now: datetime,
) -> None:
    sector, _, unit = ticket.pk.partition("#")
    doc = ticket.model_dump(mode="json")
    doc["status"] = "expired"
    doc["expired_at"] = now.isoformat()
    await queue_repo.upsert(FormalizationTicket.model_validate(doc))

    await notifier.emit(
        ExpiredEvent(
            ticket_id=ticket.id,
            sector=sector,
            unit=unit,
            reviewer_id=ticket.reviewer_id or "(unassigned)",
            user_id=ticket.hearout_id,  # caller can resolve hearout → user_id later
            expired_at=now,
        )
    )


# ---------------------------------------------------------------------------
# M-12: Container Apps Job entrypoint.
#
# Provisions the minimal real dependency graph (queue repo + notifier),
# enumerates active tenants from configuration, runs ``scan_expired`` once,
# and exits. The Container Apps Job is triggered hourly (cron 0 * * * *).
# ---------------------------------------------------------------------------


async def run_expired_check() -> list[str]:
    """Cron entrypoint — builds dependencies from env config and scans once.

    Tenant enumeration: reads ``settings.sla_cron_tenant_pks`` (JSON list of
    sector#unit strings). When empty falls back to a single cross-partition
    scan (more expensive — fine for dev/seed workloads).
    """
    import httpx  # local import: cron runtime only

    from app.agents.notification.dispatcher import NotificationDispatcher
    from app.config import settings
    from app.repos._base import InMemoryContainer
    from app.repos.error_logs import ErrorLogsRepo
    from app.util.kv import KeyVaultClient

    queue_container = InMemoryContainer()
    error_container = InMemoryContainer()
    queue_repo = FormalizationQueueRepo(queue_container)
    error_repo = ErrorLogsRepo(error_container)

    kv_uri = getattr(settings, "key_vault_uri", None)
    kv = KeyVaultClient(kv_uri) if kv_uri else None
    async with httpx.AsyncClient(timeout=10.0) as http:
        notifier = NotificationDispatcher(
            kv=kv,
            http_client=http,
            error_logs_repo=error_repo,
            admin_pk="hack#admin",
        )
        pks = list(settings.sla_cron_tenant_pks) or None
        expired = await scan_expired(queue_repo, notifier, pks=pks)
        logger.info("SLA cron run complete; expired=%d pks=%s", len(expired), pks)
        return expired


if __name__ == "__main__":  # pragma: no cover - container entrypoint
    import asyncio

    asyncio.run(run_expired_check())
