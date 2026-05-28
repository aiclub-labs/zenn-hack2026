"""POST /turn, DELETE /turn/{id}, POST /turn/{id}/ack-banner — Req 4, 7, 2.7."""
from __future__ import annotations

import logging
import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException

from app.api._deps import (
    DialogueTurnsRepoI,
    SchemaRevisionGateI,
    current_reviewer_id,
    get_delta_detector,
    get_dialogue_turns_repo,
    get_schema_gate,
)
from app.api.retrieval import retrieve_for_turn
from app.contracts.common import Role, Tenant, make_pk, utcnow
from app.contracts.cosmos import DialogueTurn
from app.contracts.http import TurnRequest, TurnResponse

router = APIRouter(prefix="/turn", tags=["turn"])
logger = logging.getLogger(__name__)


async def _append_turn(
    *,
    repo: DialogueTurnsRepoI,
    pk: str,
    session_id: str,
    role: Role,
    content: Optional[str],
    redact: bool,
    self_critic_score: Optional[float] = None,
    self_critic_reason: Optional[str] = None,
) -> tuple[str, DialogueTurn]:
    """Persist a turn doc to ``dialogue_turns``. Returns (turn_id, doc)."""
    turn_id = str(uuid.uuid4())
    doc = DialogueTurn(
        id=turn_id,
        pk=pk,
        session_id=session_id,
        turn_id=turn_id,
        role=role,
        content=None if redact else content,
        self_critic_score=self_critic_score,
        self_critic_reason=self_critic_reason,
        redact=redact,
        timestamp=utcnow(),
        schema_revision_seen_at=None,
        schema_revision_id_seen=None,
    )
    await repo.upsert(doc)
    logger.info(
        "dialogue_turns.append",
        extra={
            "pk": pk,
            "session_id": session_id,
            "turn_id": turn_id,
            "role": role,
            "redact": redact,
        },
    )
    return turn_id, doc


async def _aoai_complete(
    user_content: str, citations_ctx: list[dict[str, object]]
) -> tuple[str, float, str]:
    """Call AOAI for a structured assistant reply.

    Returns (response_text, self_critic_score, self_critic_reason).
    Score/reason are derived from a follow-up self-evaluation call kept
    intentionally lightweight (single JSON return).
    """
    from app.util.aoai_chat import chat_client, deployment_large, deployment_small

    citations_lines = "\n".join(
        f"- {c.get('citation_id', '?')}: {c.get('snippet', '')[:180]}"
        for c in citations_ctx[:5]
    ) or "(関連 record なし)"

    system = (
        "あなたは現場業務をサポートする日本語 AI アシスタントです。"
        "ユーザの質問に簡潔(2-4 文)に答え、推測した箇所は『〜と推測』と明示してください。"
        "回答冒頭に結論を1文で書き、根拠が citations にあれば言及してください。"
    )
    user_prompt = (
        f"# ユーザ質問\n{user_content}\n\n"
        f"# 関連 record (corpus 抜粋)\n{citations_lines}\n"
    )

    try:
        client = chat_client()
        resp = await client.chat.completions.create(
            model=deployment_large(),
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_completion_tokens=400,
        )
        text = (resp.choices[0].message.content or "").strip() or "(空応答)"
    except Exception as exc:  # pragma: no cover
        logger.warning("aoai.chat failed: %s", exc)
        return ("（応答生成に失敗しました）", 0.0, f"aoai_error: {exc}")

    # Lightweight self-critic: ask AOAI to grade itself 0-10.
    score, reason = 7.0, "self-critic stub"
    try:
        critic = await client.chat.completions.create(
            model=deployment_small(),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "あなたは厳格な事実性 judge です。AI応答が citations で裏付け可能か、"
                        "未記録の個人判断・過去出来事・具体数値を捏造していないかを評価します。\n"
                        "採点軸 (0-10、低いほど問題大):\n"
                        "- 0-2: citations に無い個人判断・過去の意思決定・具体値 (数値/日付/人名/型番) を断定的に答えた。"
                        "ユーザ本人しか知り得ない recall 質問に AI が答えてしまった場合は必ずこの帯。\n"
                        "- 3-4: 推測明示なく一般論で押し切った、または citations と部分的に矛盾。\n"
                        "- 5-6: 一般的フレームワーク回答で害は無いが、質問の具体性に応えていない。\n"
                        "- 7-8: citations の範囲内で答え、未記録部分は『推測』『記録なし』等で hedge。\n"
                        "- 9-10: citations を明示引用し、未知部分はユーザに確認を促した。\n"
                        "重要: citations が『(関連 record なし)』かつ質問が個人 recall (『自分はどう判断した』『何だった』"
                        "『思い出せる』等) の場合、AI が具体内容を返した時点で score ≤ 2。\n"
                        "JSON で {\"score\": float, \"reason\": str(<=80字)} のみ返答。"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"# ユーザ質問\n{user_content}\n\n"
                        f"# 提供された citations\n{citations_lines}\n\n"
                        f"# AI応答\n{text}"
                    ),
                },
            ],
            temperature=0.0,
            max_completion_tokens=120,
            response_format={"type": "json_object"},
        )
        import json as _json

        parsed = _json.loads(critic.choices[0].message.content or "{}")
        score = float(parsed.get("score", 7.0))
        reason = str(parsed.get("reason", reason))[:120]
    except Exception as exc:  # pragma: no cover
        logger.debug("self-critic failed: %s", exc)

    return (text, score, reason)


async def _run_delta_detector(turn_doc: DialogueTurn) -> Optional[str]:
    """Run delta detection inline.

    Returns the ``DeltaEvent.id`` of the first event the detector emitted,
    or None when no gap was detected (or the detector is unwired/errored).
    The id is propagated to the client so it can call ``/hearout/start``.
    Errors are swallowed so a detector outage doesn't break /turn.
    """
    logger.info(
        "delta_detector.dispatch",
        extra={"turn_id": turn_doc.turn_id, "pk": turn_doc.pk},
    )
    detector = get_delta_detector()
    if detector is None:
        logger.debug("delta_detector unwired; skipping detect()")
        return None
    try:
        events = await detector.detect(turn_doc)
    except Exception as exc:  # pragma: no cover
        logger.warning("delta_detector.detect failed: %s", exc)
        return None
    if not events:
        return None
    return events[0].id


@router.post("", response_model=TurnResponse)
async def post_turn(
    req: TurnRequest,
    gate: Annotated[SchemaRevisionGateI, Depends(get_schema_gate)],
    turns_repo: Annotated[DialogueTurnsRepoI, Depends(get_dialogue_turns_repo)],
) -> TurnResponse:
    tenant = Tenant(sector=req.sector, unit=req.unit)
    pk = tenant.pk

    # 1. user turn (content masked when redact per Req 7)
    user_turn_id, user_turn_doc = await _append_turn(
        repo=turns_repo,
        pk=pk,
        session_id=req.session_id,
        role="user",
        content=req.user_content,
        redact=req.redact,
    )

    # 2. schema revision gate (session-scoped via dialogue_turns)
    banner = await gate.banner_for(req.user_id, tenant, req.session_id)
    banner_acked = await gate.is_acked(req.user_id, tenant, req.session_id)

    # 3. retrieval (+ conflict detection, Req 8)
    citations, conflicts, prompt_ctx = await retrieve_for_turn(
        tenant=tenant, query=req.user_content, user_id=req.user_id
    )

    # 4. AOAI structured response
    ai_text, score, reason = await _aoai_complete(req.user_content, prompt_ctx)

    # 5. assistant turn
    asst_turn_id, _asst_doc = await _append_turn(
        repo=turns_repo,
        pk=pk,
        session_id=req.session_id,
        role="assistant",
        content=ai_text,
        redact=False,
        self_critic_score=score,
        self_critic_reason=reason,
    )

    # 6/7. delta detector (gated by banner ack per design §4.6).
    # Detector keys off the *user* turn (Req 12: input-time gap detection).
    # Run inline so the response can carry gap_detected (HearoutModal trigger).
    gap_event_id: Optional[str] = None
    if not req.redact and (banner is None or banner_acked):
        gap_event_id = await _run_delta_detector(user_turn_doc)
    gap_detected = gap_event_id is not None

    _ = user_turn_id
    _ = _asst_doc
    _ = conflicts  # surfaced via citations/conflicts in /retrieve sidebar

    return TurnResponse(
        turn_id=asst_turn_id,
        ai_response=ai_text,
        self_critic_score=score,
        citations=citations,
        schema_update_banner=banner,
        gap_detected=gap_detected,
        gap_event_id=gap_event_id,
    )


@router.delete("/{turn_id}")
async def delete_turn(
    turn_id: str,
    sector: str,
    unit: str,
    turns_repo: Annotated[DialogueTurnsRepoI, Depends(get_dialogue_turns_repo)],
    reviewer_id: Annotated[str, Depends(current_reviewer_id)],
) -> dict[str, bool]:
    """Req 7 — physical delete of turn + dependent delta/hearout.

    Cascade to ``delta_events`` / ``hearout_records`` is logged for now;
    those repos do not yet expose ``delete_for_turn`` and live outside
    this batch's scope (see MERGE-NOTES M-2/M-3 follow-ups).
    """
    pk = make_pk(sector, unit)
    removed = await turns_repo.delete(turn_id, pk)
    logger.info(
        "dialogue_turns.delete",
        extra={
            "turn_id": turn_id,
            "pk": pk,
            "by": reviewer_id,
            "removed": removed,
            "cascade": "pending_delta_events_hearout_records",
        },
    )
    return {"ok": removed}


@router.post("/{turn_id}/ack-banner")
async def ack_banner(
    turn_id: str,
    sector: str,
    unit: str,
    user_id: str,
    gate: Annotated[SchemaRevisionGateI, Depends(get_schema_gate)],
    turns_repo: Annotated[DialogueTurnsRepoI, Depends(get_dialogue_turns_repo)],
) -> dict[str, bool]:
    tenant = Tenant(sector=sector, unit=unit)
    pk = tenant.pk
    turn = await turns_repo.get(turn_id, pk)
    if turn is None:
        raise HTTPException(status_code=404, detail="turn not found")
    session_id = turn.session_id
    try:
        await gate.acknowledge(user_id, tenant, session_id, turn_id)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"ok": True}
