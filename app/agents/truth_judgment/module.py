"""Truth Judgment module (Req 14).

Pipeline:
  1. GraphCheck — decompose the record content (5W1H concatenation) into
     atomic factual claims via gpt-4o-mini.
  2. Per-claim evidence retrieval — vector query AI Search corpus.
  3. If results >= 3 → vote based on hybrid retrieval; otherwise cold-start
     fallback to FactCheck 3-LLM ensemble (gpt-4o, gpt-4o-mini, gpt-4o)
     with different temperatures, majority vote.
  4. Aggregate per-claim verdicts → record verdict:
       - all supported → supported
       - any conflict → conflict
       - mixed novel/supported → novel
  5. Persist TruthJudgmentLog (pattern="input-time").
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from collections import Counter
from typing import Any, Optional

from openai import AsyncAzureOpenAI

from app.agents.truth_judgment.prompts import (
    FACTCHECK_SYSTEM,
    GRAPHCHECK_SYSTEM,
    factcheck_user,
    graphcheck_user,
)
from app.contracts.common import TJVerdict, Tenant
from app.contracts.cosmos import HearoutRecord, TruthJudgmentLog
from app.repos.truth_judgment_logs import TruthJudgmentLogsRepo
from app.util.aisearch import CorpusIndex
from app.util.embedding import embed

logger = logging.getLogger(__name__)

_COLD_START_THRESHOLD = 3


def _flatten_record(record: HearoutRecord) -> str:
    parts: list[str] = []
    for k in ("who", "what", "when", "where", "why", "how"):
        v = getattr(record, k, None)
        if v:
            parts.append(f"{k}: {v}")
    return "\n".join(parts) or "(no slots)"


class TruthJudgmentModule:
    """Implements `TruthJudgmentI`."""

    def __init__(
        self,
        tj_log_repo: TruthJudgmentLogsRepo,
        corpus: CorpusIndex,
        llm_client: AsyncAzureOpenAI,
    ) -> None:
        self._logs = tj_log_repo
        self._corpus = corpus
        self._llm = llm_client
        self._small = os.getenv("AOAI_DEPLOYMENT_GPT4OMINI", "gpt-4o-mini")
        self._large = os.getenv("AOAI_DEPLOYMENT_GPT4O", "gpt-4o")

    async def judge(self, record: HearoutRecord) -> TruthJudgmentLog:
        sector, unit = record.pk.split("#", 1)
        tenant = Tenant(sector=sector, unit=unit)
        content = _flatten_record(record)

        claims = await self._decompose(content)
        ensemble_votes: list[dict[str, Any]] = []
        claim_verdicts: list[TJVerdict] = []
        evidence_scores: list[float] = []

        for claim in claims:
            claim_vec = await embed(claim)
            hits = await self._corpus.query(
                tenant=tenant,
                query_vec=claim_vec,
                top_k=5,
            )
            evidence_scores.append(min(1.0, len(hits) / 5.0))
            if len(hits) >= _COLD_START_THRESHOLD:
                verdict, vote_meta = await self._vote_from_hits(claim, hits)
            else:
                verdict, vote_meta = await self._ensemble_factcheck(claim, hits)
            claim_verdicts.append(verdict)
            ensemble_votes.append({"claim": claim, "verdict": verdict, **vote_meta})

        record_verdict = self._aggregate(claim_verdicts)
        evidence_score = sum(evidence_scores) / max(1, len(evidence_scores))

        log = TruthJudgmentLog(
            id=f"tj_{uuid.uuid4().hex[:24]}",
            pk=record.pk,
            record_id=record.id,
            atomic_claims=claims,
            evidence_score=round(evidence_score, 4),
            ensemble_votes=ensemble_votes,
            verdict=record_verdict,
            pattern="input-time",
        )
        await self._logs.append(log)
        return log

    # ------------------------------------------------------------------
    async def _decompose(self, content: str) -> list[str]:
        try:
            resp = await self._llm.chat.completions.create(
                model=self._small,
                temperature=0.0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": GRAPHCHECK_SYSTEM},
                    {"role": "user", "content": graphcheck_user(content)},
                ],
            )
            data = json.loads(resp.choices[0].message.content or "{}")
            claims = data.get("atomic_claims") or []
            return [str(c).strip() for c in claims if str(c).strip()][:8]
        except Exception as exc:  # pragma: no cover
            logger.warning("graphcheck failed: %s", exc)
            return [content[:200]]

    async def _vote_from_hits(
        self, claim: str, hits: list[dict[str, Any]]
    ) -> tuple[TJVerdict, dict[str, Any]]:
        """Vote by examining retrieved corpus entries.

        Quick heuristic for MVP: if multiple hits exist with diverging
        content (signaled by `superseded_by` or `coexisting_views`), → conflict.
        Otherwise supported."""
        diverging = sum(
            1 for h in hits if h.get("superseded_by") or h.get("coexisting_views")
        )
        verdict: TJVerdict
        if diverging >= 2:
            verdict = "conflict"
        else:
            verdict = "supported"
        return verdict, {"source": "retrieval", "hits": len(hits)}

    async def _ensemble_factcheck(
        self, claim: str, hits: list[dict[str, Any]]
    ) -> tuple[TJVerdict, dict[str, Any]]:
        """3-LLM ensemble majority vote when corpus is cold."""
        evidence = [str(h.get("content", "")) for h in hits if h.get("content")]
        configs = [
            (self._large, 0.0),
            (self._small, 0.2),
            (self._large, 0.6),
        ]
        votes: list[TJVerdict] = []
        per_call: list[dict[str, Any]] = []
        for model, temp in configs:
            v, meta = await self._single_factcheck(claim, evidence, model, temp)
            votes.append(v)
            per_call.append({"model": model, "temperature": temp, **meta})

        counter = Counter(votes)
        majority: TJVerdict
        if counter["conflict"] >= 2:
            majority = "conflict"
        elif counter["supported"] >= 2:
            majority = "supported"
        else:
            majority = "novel"
        return majority, {"source": "ensemble", "votes": per_call}

    async def _single_factcheck(
        self, claim: str, evidence: list[str], model: str, temperature: float
    ) -> tuple[TJVerdict, dict[str, Any]]:
        try:
            resp = await self._llm.chat.completions.create(
                model=model,
                temperature=temperature,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": FACTCHECK_SYSTEM},
                    {"role": "user", "content": factcheck_user(claim, evidence)},
                ],
            )
            data = json.loads(resp.choices[0].message.content or "{}")
            raw_v = str(data.get("verdict", "novel"))
            verdict: TJVerdict = (
                raw_v if raw_v in ("supported", "novel", "conflict") else "novel"
            )
            return verdict, {
                "confidence": float(data.get("confidence", 0.0)),
                "reason": str(data.get("reason", ""))[:240],
            }
        except Exception as exc:  # pragma: no cover
            logger.warning("factcheck (%s) failed: %s", model, exc)
            return "novel", {"error": str(exc)}

    @staticmethod
    def _aggregate(verdicts: list[TJVerdict]) -> TJVerdict:
        if not verdicts:
            return "novel"
        if any(v == "conflict" for v in verdicts):
            return "conflict"
        if all(v == "supported" for v in verdicts):
            return "supported"
        return "novel"
