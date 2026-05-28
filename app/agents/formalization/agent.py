"""Formalization Agent (Req 13).

Responsibilities (MVP):
  - weight(record): a = self_critic/10, b=c=1.0 → final = a/10 invariant per design §4.5
  - submit_for_review: branch on final threshold and TJ verdict
  - on_review_decision: approve / edit / reject side-effects
  - on_conflict_decision: adopt_new / keep_existing / coexist
"""
from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Optional

from app.agents.truth_judgment.module import TruthJudgmentModule
from app.contracts.agents import (
    ConflictResolution,
    CorpusUpsertResult,
    NotificationDispatcherI,
)
from app.contracts.common import ConflictDecision, ReviewDecision, TJVerdict
from app.contracts.cosmos import (
    CitationAuditEntry,
    CorpusMeta,
    DeltaEvent,
    FormalizationTicket,
    HearoutRecord,
)
from app.contracts.events import ExpiredEvent, PendingReviewEvent
from app.repos.citation_audit_log import CitationAuditLogRepo
from app.repos.corpus_meta import CorpusMetaRepo
from app.repos.delta_events import DeltaEventsRepo
from app.repos.formalization_queue import FormalizationQueueRepo
from app.repos.hearout_records import HearoutRecordsRepo
from app.util.aisearch import CorpusIndex
from app.util.embedding import embed

logger = logging.getLogger(__name__)

_THRESHOLD = 0.5
_REJECT_COOLDOWN_DAYS = 7


def _flatten(record: HearoutRecord) -> str:
    parts: list[str] = []
    for k in ("who", "what", "when", "where", "why", "how"):
        v = getattr(record, k, None)
        if v:
            parts.append(f"{k}: {v}")
    return "\n".join(parts) or ""


class FormalizationAgent:
    """Implements `FormalizationAgentI`."""

    def __init__(
        self,
        queue_repo: FormalizationQueueRepo,
        hearout_repo: HearoutRecordsRepo,
        corpus_meta_repo: CorpusMetaRepo,
        citation_audit_repo: CitationAuditLogRepo,
        delta_events_repo: DeltaEventsRepo,
        corpus: CorpusIndex,
        truth_judgment: TruthJudgmentModule,
        notifier: NotificationDispatcherI,
        user_resolver: Optional[Callable[[str, str], Awaitable[str]]] = None,
        schema_field_resolver: Optional[Callable[[str, str], Awaitable[str]]] = None,
    ) -> None:
        self._queue = queue_repo
        self._hearouts = hearout_repo
        self._corpus_meta = corpus_meta_repo
        self._citation_audit = citation_audit_repo
        self._delta_events = delta_events_repo
        self._corpus = corpus
        self._tj = truth_judgment
        self._notifier = notifier
        # M-3: gap_event_id -> originating user_id resolver. When unset we
        # fall back to the placeholder behaviour (gap_event_id) so existing
        # tests keep passing.
        self._resolve_user = user_resolver
        # M-4: gap_event_id -> schema_field_id resolver for corpus back-fill.
        self._resolve_schema_field = schema_field_resolver

    # ------------------------------------------------------------------
    async def weight(
        self, record: HearoutRecord
    ) -> tuple[float, float, float, float]:
        # MVP: extract record-level self-critic from persisted extra state if any
        raw = await self._hearouts.get_raw(record.id, record.pk)
        a_raw = 0.0
        if raw is not None:
            a_raw = float(raw.get("session_self_critic", 0.0))
        if a_raw <= 0.0:
            # fallback: outcome-derived
            a_raw = {"completed": 6.0, "skipped": 1.0, "expired": 2.0}.get(
                record.outcome, 1.0
            )
        a = max(0.0, min(10.0, a_raw))
        b = 1.0
        c = 1.0
        final = a / 10.0
        return (a, b, c, final)

    # ------------------------------------------------------------------
    async def submit_for_review(
        self,
        record: HearoutRecord,
        weights: tuple[float, float, float, float],
        tj_verdict: Optional[TJVerdict],
    ) -> FormalizationTicket:
        a, b, c, final = weights
        sector, unit = record.pk.split("#", 1)
        ticket_id = f"ft_{uuid.uuid4().hex[:24]}"
        now = datetime.now(timezone.utc)

        # Determine status & whether to run TJ first
        if final < _THRESHOLD:
            status = "pending_review"
            verdict_for_doc = tj_verdict
        else:
            # Need TJ first to decide normal vs conflict queue
            if tj_verdict is None:
                tj_log = await self._tj.judge(record)
                verdict_for_doc = tj_log.verdict
            else:
                verdict_for_doc = tj_verdict
            status = (
                "conflict_pending" if verdict_for_doc == "conflict" else "pending_review"
            )

        ticket = FormalizationTicket(
            id=ticket_id,
            pk=record.pk,
            hearout_id=record.id,
            weight_a=a,
            weight_b=b,
            weight_c=c,
            weight_final=final,
            tj_verdict=verdict_for_doc,
            status=status,
            locked_by=None,
            lock_expires_at=None,
            reviewer_id=None,
            decision=None,
            conflict_decision=None,
            edit_diff=None,
            expired_at=None,
            created_at=now,
        )
        await self._queue.upsert(ticket)

        # Req 13.5 — notify user when forced into pending due to low weight
        if final < _THRESHOLD:
            resolved_user_id = record.gap_event_id  # placeholder fallback
            if self._resolve_user is not None:
                try:
                    resolved_user_id = await self._resolve_user(
                        record.gap_event_id, record.pk
                    )
                except Exception as exc:  # pragma: no cover — defensive
                    logger.warning(
                        "user_resolver failed for gap_event %s: %s",
                        record.gap_event_id, exc,
                    )
            await self._notifier.emit(
                PendingReviewEvent(
                    ticket_id=ticket_id,
                    sector=sector,
                    unit=unit,
                    user_id=resolved_user_id,
                    weight_final=final,
                    reason=f"final weight {final:.2f} < {_THRESHOLD}",
                )
            )
        return ticket

    # ------------------------------------------------------------------
    async def on_review_decision(
        self,
        ticket_id: str,
        pk: str,
        decision: ReviewDecision,
        edited: Optional[HearoutRecord] = None,
    ) -> CorpusUpsertResult:
        ticket = await self._queue.get(ticket_id, pk)
        if ticket is None:
            raise ValueError(f"ticket not found: {ticket_id}")

        record = edited or await self._hearouts.get(ticket.hearout_id, pk)
        if record is None:
            raise ValueError(f"hearout record not found: {ticket.hearout_id}")

        if decision == "edit" and edited is not None:
            # Req 14.6 — re-run TJ on edited content
            tj_log = await self._tj.judge(edited)
            # If edit flipped to conflict, route to conflict queue
            if tj_log.verdict == "conflict":
                doc = ticket.model_dump(mode="json")
                doc["status"] = "conflict_pending"
                doc["tj_verdict"] = "conflict"
                doc["decision"] = "edit"
                await self._queue.upsert(FormalizationTicket.model_validate(doc))
                return CorpusUpsertResult(record_id=record.id, corpus_meta_id="")

        if decision == "reject":
            # Set cooldown_until on the originating delta event(s)
            await self._apply_reject_cooldown(record)
            doc = ticket.model_dump(mode="json")
            doc["status"] = "rejected"
            doc["decision"] = "reject"
            await self._queue.upsert(FormalizationTicket.model_validate(doc))
            return CorpusUpsertResult(record_id=record.id, corpus_meta_id="")

        # approve (or edit that survived TJ)
        return await self._approve_and_upsert(ticket, record)

    # ------------------------------------------------------------------
    async def on_conflict_decision(
        self, ticket_id: str, pk: str, decision: ConflictDecision
    ) -> ConflictResolution:
        ticket = await self._queue.get(ticket_id, pk)
        if ticket is None:
            raise ValueError(f"ticket not found: {ticket_id}")
        record = await self._hearouts.get(ticket.hearout_id, pk)
        if record is None:
            raise ValueError(f"hearout record not found: {ticket.hearout_id}")

        affected: list[str] = [record.id]
        existing_ids = await self._find_conflicting_record_ids(record)

        if decision == "adopt_new":
            for old_id in existing_ids:
                await self._corpus_meta.set_superseded(old_id, pk, superseded_by=record.id)
                await self._citation_audit.append(
                    CitationAuditEntry(
                        id=f"ca_{uuid.uuid4().hex[:24]}",
                        pk=pk,
                        old_record_id=old_id,
                        new_record_id=record.id,
                        transition="superseded",
                        occurred_at=datetime.now(timezone.utc),
                    )
                )
                affected.append(old_id)
            await self._approve_and_upsert(ticket, record, status_override="approved")
        elif decision == "keep_existing":
            doc = ticket.model_dump(mode="json")
            doc["status"] = "rejected"
            doc["conflict_decision"] = "keep_existing"
            await self._queue.upsert(FormalizationTicket.model_validate(doc))
        else:  # coexist
            new_meta_id = await self._approve_and_upsert(
                ticket, record, status_override="approved"
            )
            # mark mutual coexisting on both sides
            for old_id in existing_ids:
                await self._corpus_meta.add_coexisting(old_id, pk, [record.id])
                await self._corpus_meta.add_coexisting(
                    new_meta_id.corpus_meta_id, pk, [old_id]
                )
                await self._citation_audit.append(
                    CitationAuditEntry(
                        id=f"ca_{uuid.uuid4().hex[:24]}",
                        pk=pk,
                        old_record_id=old_id,
                        new_record_id=record.id,
                        transition="coexists",
                        occurred_at=datetime.now(timezone.utc),
                    )
                )
                affected.append(old_id)

        doc = ticket.model_dump(mode="json")
        doc["conflict_decision"] = decision
        if decision != "keep_existing":
            doc["status"] = "approved"
        await self._queue.upsert(FormalizationTicket.model_validate(doc))

        return ConflictResolution(
            ticket_id=ticket_id, decision=decision, affected_record_ids=affected
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    async def _approve_and_upsert(
        self,
        ticket: FormalizationTicket,
        record: HearoutRecord,
        status_override: Optional[str] = None,
    ) -> CorpusUpsertResult:
        content = _flatten(record)
        vec = await embed(content)
        sector, unit = record.pk.split("#", 1)
        corpus_meta_id = f"cm_{uuid.uuid4().hex[:24]}"
        now = datetime.now(timezone.utc)

        # M-4: back-fill schema_field_id from the originating delta event.
        schema_field_id = ""
        if self._resolve_schema_field is not None and record.gap_event_id:
            try:
                schema_field_id = await self._resolve_schema_field(
                    record.gap_event_id, record.pk
                ) or ""
            except Exception as exc:  # pragma: no cover — defensive
                logger.warning(
                    "schema_field_resolver failed for gap_event %s: %s",
                    record.gap_event_id, exc,
                )

        await self._corpus.upsert(
            {
                "id": record.id,
                "sector": sector,
                "unit": unit,
                "pk": record.pk,
                "schema_field_id": schema_field_id,
                "content": content,
                "atomic_claims": [],
                "weight_final": ticket.weight_final,
                "shareability": "private",
                "is_active": True,
                "superseded_by": "",
                "created_at": now.isoformat(),
                "vector": vec,
            }
        )

        await self._corpus_meta.upsert(
            CorpusMeta(
                id=corpus_meta_id,
                pk=record.pk,
                record_id=record.id,
                schema_field_id=schema_field_id,
                referenced_count=0,
                last_referenced_at=None,
                shareability="private",
                is_active=True,
                superseded_by=None,
                coexisting_views=None,
            )
        )
        await self._citation_audit.append(
            CitationAuditEntry(
                id=f"ca_{uuid.uuid4().hex[:24]}",
                pk=record.pk,
                old_record_id="",
                new_record_id=record.id,
                transition="created",
                occurred_at=now,
            )
        )

        doc = ticket.model_dump(mode="json")
        doc["status"] = status_override or "approved"
        doc["decision"] = "approve" if doc.get("decision") != "edit" else "edit"
        await self._queue.upsert(FormalizationTicket.model_validate(doc))

        return CorpusUpsertResult(record_id=record.id, corpus_meta_id=corpus_meta_id)

    async def _find_conflicting_record_ids(self, record: HearoutRecord) -> list[str]:
        """Vector-search the corpus for likely conflicting peers."""
        sector, unit = record.pk.split("#", 1)
        from app.contracts.common import Tenant

        vec = await embed(_flatten(record))
        hits = await self._corpus.query(
            tenant=Tenant(sector=sector, unit=unit),
            query_vec=vec,
            top_k=3,
        )
        return [str(h["id"]) for h in hits if h.get("id") and h["id"] != record.id]

    async def _apply_reject_cooldown(self, record: HearoutRecord) -> None:
        # The originating gap event is referenced via record.gap_event_id
        # We persist a fresh DeltaEvent marker carrying the cooldown_until field.
        cooldown_until = datetime.now(timezone.utc) + timedelta(days=_REJECT_COOLDOWN_DAYS)
        marker = DeltaEvent(
            id=f"de_reject_{uuid.uuid4().hex[:16]}",
            pk=record.pk,
            turn_id=record.session_id,  # session-scoped placeholder
            schema_field_id=None,
            self_critic=0.0,
            distance=0.0,
            gap_detected=False,
            cooldown_until=cooldown_until,
            matched_reason=f"reject-cooldown from {record.id}",
        )
        await self._delta_events.append(marker)
