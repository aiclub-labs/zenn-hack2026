"""Hearout Agent (Req 5).

Drives the 5W1H interview as a HITL loop. MAF 1.0 `RequestInfoEvent` is the
externally-facing pattern; for the MVP backend we expose a thin
start/respond/skip API that the FastAPI layer (WT-E) brokers between user UI
and the agent.

Status transitions:
  start()        → in_progress  (returns next_question)
  respond(text)  → in_progress | completed | expired
  respond("SKIP") → skipped
  skip()         → skipped (idempotent shortcut)
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from typing import Any, Optional

from openai import AsyncAzureOpenAI

from app.agents.hearout.prompts import (
    HEAROUT_SYSTEM,
    INITIAL_QUESTION_FALLBACK,
    user_prompt,
)
from app.agents.hearout.state import HearoutSessionState
from app.contracts.agents import HearoutTurn
from app.contracts.common import HearoutOutcome, Tenant
from app.contracts.cosmos import HearoutRecord
from app.repos.hearout_records import HearoutRecordsRepo

logger = logging.getLogger(__name__)

_MAX_TURNS = 5


class HearoutAgent:
    """Implements `HearoutAgentI`."""

    def __init__(
        self,
        hearout_repo: HearoutRecordsRepo,
        llm_client: AsyncAzureOpenAI,
    ) -> None:
        self._repo = hearout_repo
        self._llm = llm_client
        self._deployment = os.getenv("AOAI_DEPLOYMENT_GPT4O", "gpt-4o")

    # ------------------------------------------------------------------
    async def start(
        self, gap_event_id: str, user_id: str, tenant: Tenant
    ) -> HearoutTurn:
        record_id = f"ho_{uuid.uuid4().hex[:24]}"
        session_id = f"hosess_{uuid.uuid4().hex[:16]}"
        state = HearoutSessionState(
            record_id=record_id,
            pk=tenant.pk,
            gap_event_id=gap_event_id,
            session_id=session_id,
            user_id=user_id,
            status="in_progress",
            turn_count=0,
        )
        llm_out = await self._call_llm(state, latest_answer=None)
        state.turn_count = 1
        state.transcript.append({"role": "assistant", "content": llm_out["next_question"] or INITIAL_QUESTION_FALLBACK})
        state.next_question = llm_out["next_question"] or INITIAL_QUESTION_FALLBACK
        state.slots = llm_out["slots"]
        state.self_critic = llm_out["self_critic"]

        await self._persist(state, outcome="completed" if llm_out["complete"] else "expired", final=False)
        self._mem_cache[state.record_id] = state
        self._pk_hint[state.record_id] = state.pk
        return HearoutTurn(
            session_id=state.record_id,
            status=state.status,
            next_question=state.next_question,
            final_record=None,
            turn_count=state.turn_count,
        )

    async def respond(self, session_id: str, answer: str) -> HearoutTurn:
        # `session_id` here is the record_id (HearoutTurn.session_id we returned).
        state = await self._load(session_id)
        if state is None:
            raise ValueError(f"hearout session not found: {session_id}")
        if state.status != "in_progress":
            return self._to_turn(state, final_record=await self._build_record(state, state.status))

        if answer.strip().upper() == "SKIP":
            return await self._terminate(state, "skipped")

        state.transcript.append({"role": "user", "content": answer})
        llm_out = await self._call_llm(state, latest_answer=answer)
        state.slots = llm_out["slots"]
        state.self_critic = llm_out["self_critic"]
        state.turn_count += 1

        completed = bool(llm_out["complete"])
        next_q = llm_out["next_question"]
        if state.turn_count >= _MAX_TURNS and not completed:
            return await self._terminate(state, "expired")
        if completed:
            return await self._terminate(state, "completed")

        state.next_question = next_q or INITIAL_QUESTION_FALLBACK
        state.transcript.append({"role": "assistant", "content": state.next_question})
        # M-2: persist intermediate state on every respond() so any replica
        # can rehydrate from Cosmos (hearout_records is source of truth).
        await self._persist(state, outcome="expired", final=False)
        self._mem_cache[state.record_id] = state
        return self._to_turn(state, final_record=None)

    async def skip(self, session_id: str) -> HearoutRecord:
        state = await self._load(session_id)
        if state is None:
            raise ValueError(f"hearout session not found: {session_id}")
        if state.status != "in_progress":
            return await self._build_record(state, state.status)
        await self._terminate(state, "skipped")
        return await self._build_record(state, "skipped")

    # ------------------------------------------------------------------
    async def _terminate(self, state: HearoutSessionState, outcome: HearoutOutcome) -> HearoutTurn:
        state.status = outcome  # HearoutOutcome is a subset of HearoutStatus
        state.next_question = None
        record = await self._build_record(state, outcome)
        await self._persist(state, outcome=outcome, final=True, record=record)
        return self._to_turn(state, final_record=record)

    def _to_turn(
        self, state: HearoutSessionState, final_record: Optional[HearoutRecord]
    ) -> HearoutTurn:
        return HearoutTurn(
            session_id=state.record_id,
            status=state.status,
            next_question=state.next_question,
            final_record=final_record,
            turn_count=state.turn_count,
        )

    async def _build_record(
        self, state: HearoutSessionState, outcome: HearoutOutcome
    ) -> HearoutRecord:
        slots = state.slots or {}
        return HearoutRecord(
            id=state.record_id,
            pk=state.pk,
            gap_event_id=state.gap_event_id,
            session_id=state.session_id,
            transcript=list(state.transcript),
            who=slots.get("who"),
            what=slots.get("what"),
            when=slots.get("when"),
            where=slots.get("where"),
            why=slots.get("why"),
            how=slots.get("how"),
            outcome=outcome,
            turn_count=state.turn_count,
        )

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    async def _persist(
        self,
        state: HearoutSessionState,
        outcome: HearoutOutcome,
        final: bool,
        record: Optional[HearoutRecord] = None,
    ) -> None:
        if record is None:
            record = await self._build_record(state, outcome)
        extra = state.to_extra()
        extra["transcript_full"] = list(state.transcript)  # retain interim if needed
        extra["slots"] = dict(state.slots)
        extra["turn_count"] = state.turn_count
        extra["gap_event_id"] = state.gap_event_id
        extra["session_id_internal"] = state.session_id
        if final:
            extra["status"] = outcome
        else:
            # M-2: in-flight rows carry status=in_progress so rehydration
            # logic can distinguish resumable from terminal records.
            extra["status"] = "in_progress"
        await self._repo.upsert(record, extra_state=extra)

    async def _load(self, record_id: str) -> Optional[HearoutSessionState]:
        """Resolve session state for ``record_id``.

        Lookup order (M-2):
          1. process-local ``_mem_cache`` (hot path, same replica)
          2. ``_pk_hint`` → ``hydrate_from_repo`` (cold replica / restart)
        """
        cached = self._mem_cache.get(record_id)
        if cached is not None:
            return cached
        pk = self._pk_hint.get(record_id)
        if pk is None:
            logger.warning(
                "hearout._load: no pk hint for %s; cannot rehydrate from Cosmos",
                record_id,
            )
            return None
        hydrated = await self.hydrate_from_repo(record_id, pk)
        if hydrated is not None:
            self._mem_cache[record_id] = hydrated
        return hydrated

    async def hydrate_from_repo(
        self, session_id: str, pk: str
    ) -> Optional[HearoutSessionState]:
        """Rebuild ``HearoutSessionState`` from the persisted Cosmos doc.

        Returns None if no row exists. Used after replica restart / when
        the in-process cache misses (Container Apps multi-replica safety).
        """
        raw = await self._repo.get_by_session(session_id, pk)
        if raw is None:
            return None
        slots_raw = raw.get("slots") or {}
        # Reconstruct slots from either the explicit "slots" extra or the
        # frozen contract fields (who/what/...).
        slots: dict[str, Optional[str]] = {
            k: slots_raw.get(k) if slots_raw else raw.get(k)
            for k in ("who", "what", "when", "where", "why", "how")
        }
        transcript = list(raw.get("transcript_full") or raw.get("transcript") or [])
        status = raw.get("status") or "in_progress"
        state = HearoutSessionState(
            record_id=raw["id"],
            pk=raw["pk"],
            gap_event_id=raw.get("gap_event_id", ""),
            session_id=raw.get("session_id_internal") or raw.get("session_id", ""),
            user_id=raw.get("user_id", ""),
            status=status,
            turn_count=int(raw.get("turn_count", 0)),
            transcript=transcript,
            slots=slots,
            next_question=raw.get("next_question"),
            self_critic=float(raw.get("session_self_critic", 0.0)),
        )
        self._pk_hint[session_id] = pk
        return state

    _mem_cache: dict[str, HearoutSessionState] = {}
    _pk_hint: dict[str, str] = {}

    async def _call_llm(
        self, state: HearoutSessionState, latest_answer: Optional[str]
    ) -> dict[str, Any]:
        sector, unit = state.pk.split("#", 1)
        prompt = user_prompt(
            gap_event_id=state.gap_event_id,
            sector=sector,
            unit=unit,
            turn_count=state.turn_count + 1,
            transcript=state.transcript,
            latest_answer=latest_answer,
        )
        try:
            resp = await self._llm.chat.completions.create(
                model=self._deployment,
                temperature=0.3,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": HEAROUT_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
            )
            data = json.loads(resp.choices[0].message.content or "{}")
        except Exception as exc:  # pragma: no cover
            logger.warning("hearout LLM failed: %s", exc)
            data = {}
        return {
            "slots": data.get("slots") or {},
            "next_question": data.get("next_question"),
            "complete": bool(data.get("complete", False)),
            "self_critic": float(data.get("self_critic", 0.0)),
            "chat_extract_summary": data.get("chat_extract_summary", ""),
        }
