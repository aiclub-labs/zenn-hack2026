"""Delta Detector Agent (Req 12).

Inputs:  DialogueTurn (user role)
Outputs: list[DeltaEvent] — one per matched active schema field.

Gap rule (Req 12.3-12.4):
  gap = (self_critic < 3.0) OR (3.0 <= self_critic <= 6.5 AND distance > 0.4)

Cooldown (Req 12.5-12.7):
  7-day cooldown per (schema_field_id, session_id) after a gap fires.
  Suppress 3 consecutive turns in the same session for the same field; on the
  4th turn, re-fire even if cooldown_until is still in the future.

Redact (Req 12.8 / Req 7):
  If turn.redact is True → return [] with no Cosmos writes.

Out-of-schema (Req 12.9-12.10):
  If no field matched at all → append to schema_candidate_log via LLM.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import uuid
from typing import Any, Optional

from openai import AsyncAzureOpenAI

from app.agents.delta_detector.prompts import (
    SCHEMA_CANDIDATE_SYSTEM,
    SCHEMA_CANDIDATE_USER,
)
from app.contracts.cosmos import DeltaEvent, DialogueTurn, SchemaFieldDoc
from app.repos.delta_events import DeltaEventsRepo
from app.repos.schema_candidate_log import SchemaCandidateLogRepo
from app.util.embedding import cosine_distance, embed

logger = logging.getLogger(__name__)

_DISTANCE_THRESHOLD = 0.4
_SELF_CRITIC_HARD_GAP = 3.0
_SELF_CRITIC_SOFT_HIGH = 6.5
_CONSECUTIVE_SUPPRESS = 3  # Req 12.6


def _matched_reason(self_critic: float, distance: float, gap: bool) -> str:
    if not gap:
        return f"no-gap sc={self_critic:.2f} d={distance:.2f}"
    if self_critic < _SELF_CRITIC_HARD_GAP:
        return f"hard-gap sc={self_critic:.2f}"
    return f"soft-gap sc={self_critic:.2f} d={distance:.2f}"


class DeltaDetectorAgent:
    """Implements `DeltaDetectorAgentI`."""

    def __init__(
        self,
        delta_events_repo: DeltaEventsRepo,
        schema_candidate_repo: SchemaCandidateLogRepo,
        load_active_schemas: Any,  # async callable: (pk) -> list[SchemaFieldDoc]
        recent_session_turn_ids: Any,  # async callable: (pk, session_id, limit) -> list[str]
        llm_client: Optional[AsyncAzureOpenAI] = None,
    ) -> None:
        self._delta_events = delta_events_repo
        self._schema_candidates = schema_candidate_repo
        self._load_active_schemas = load_active_schemas
        self._recent_turn_ids = recent_session_turn_ids
        self._llm = llm_client
        self._small_deployment = os.getenv("AOAI_DEPLOYMENT_GPT4OMINI", "gpt-4o-mini")

    # ------------------------------------------------------------------
    # Public protocol
    # ------------------------------------------------------------------
    async def detect(self, turn: DialogueTurn) -> list[DeltaEvent]:
        # Req 12.8 / Req 7
        if turn.redact or not turn.content:
            return []
        if turn.role != "user":
            return []

        schemas: list[SchemaFieldDoc] = await self._load_active_schemas(turn.pk)
        if not schemas:
            return []

        turn_vec = await embed(turn.content)
        self_critic = float(turn.self_critic_score or 0.0)

        # session-scoped recent delta_events for cooldown / consecutive checks
        recent_turn_ids: list[str] = await self._recent_turn_ids(
            turn.pk, turn.session_id, _CONSECUTIVE_SUPPRESS + 2
        )

        events: list[DeltaEvent] = []
        matched_any = False
        for field in schemas:
            base_vec = await embed(field.ai_baseline_assumption or field.description)
            distance = cosine_distance(turn_vec, base_vec)

            gap = self._gap_rule(self_critic, distance)
            matched_any = matched_any or (distance < 0.7)  # loose "matched" gate

            # Cooldown / consecutive suppression — only relevant when about to fire
            should_persist = True
            if gap:
                should_persist = await self._respect_cooldown(
                    turn.pk, field.id, turn.session_id, recent_turn_ids
                )

            event = DeltaEvent(
                id=f"de_{uuid.uuid4().hex[:24]}",
                pk=turn.pk,
                turn_id=turn.turn_id,
                schema_field_id=field.id,
                self_critic=self_critic,
                distance=distance,
                gap_detected=gap and should_persist,
                cooldown_until=(
                    self._delta_events.default_cooldown_until()
                    if (gap and should_persist)
                    else None
                ),
                matched_reason=_matched_reason(self_critic, distance, gap and should_persist),
            )
            if gap and should_persist:
                await self._delta_events.append(event)
                events.append(event)

        # Req 12.9 — totally out of schema → log candidate
        if not matched_any:
            await self._log_schema_candidate(turn)

        return events

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    @staticmethod
    def _gap_rule(self_critic: float, distance: float) -> bool:
        if self_critic < _SELF_CRITIC_HARD_GAP:
            return True
        if (
            _SELF_CRITIC_HARD_GAP <= self_critic <= _SELF_CRITIC_SOFT_HIGH
            and distance > _DISTANCE_THRESHOLD
        ):
            return True
        return False

    async def _respect_cooldown(
        self,
        pk: str,
        field_id: str,
        session_id: str,
        recent_turn_ids: list[str],
    ) -> bool:
        """Return True if we should persist (not suppressed)."""
        # Check session-scoped consecutive-suppression first (Req 12.6-12.7)
        recent = await self._delta_events.list_recent_for_session(
            pk, recent_turn_ids, schema_field_id=field_id, limit=_CONSECUTIVE_SUPPRESS
        )
        consecutive = sum(1 for e in recent if e.gap_detected)
        if consecutive >= _CONSECUTIVE_SUPPRESS:
            # 3 consecutive already fired in this session → re-fire (override cooldown)
            return True

        cooldown = await self._delta_events.get_cooldown(pk, field_id)
        if cooldown is not None:
            return False
        return True

    async def _log_schema_candidate(self, turn: DialogueTurn) -> None:
        if self._llm is None:
            # Cheap fallback: hint from first 30 chars
            content = turn.content or ""
            hint = hashlib.sha1(content.encode("utf-8")).hexdigest()[:12]
            await self._schema_candidates.upsert(
                pk=turn.pk,
                turn_id=turn.turn_id,
                suggested_field_hint=f"candidate_{hint}",
                llm_reason="(no LLM client wired; using hash fallback)",
            )
            return

        sector, unit = turn.pk.split("#", 1)
        msg_user = SCHEMA_CANDIDATE_USER.format(
            sector=sector,
            unit=unit,
            content=(turn.content or "")[:600],
            self_critic=turn.self_critic_score or 0.0,
            active_count=0,
        )
        try:
            resp = await self._llm.chat.completions.create(
                model=self._small_deployment,
                temperature=0.2,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SCHEMA_CANDIDATE_SYSTEM},
                    {"role": "user", "content": msg_user},
                ],
            )
            content = resp.choices[0].message.content or "{}"
            data: dict[str, Any] = json.loads(content)
            hint = str(data.get("suggested_field_hint", "")).strip() or "unnamed_field"
            reason = str(data.get("llm_reason", "")).strip() or "LLM did not provide reason"
        except Exception as exc:  # pragma: no cover — defensive
            logger.warning("schema_candidate LLM failed: %s", exc)
            hint = "unnamed_field"
            reason = f"LLM error: {exc}"

        await self._schema_candidates.upsert(
            pk=turn.pk,
            turn_id=turn.turn_id,
            suggested_field_hint=hint,
            llm_reason=reason,
        )
