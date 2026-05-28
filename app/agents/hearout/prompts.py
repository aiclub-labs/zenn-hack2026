"""Kunumi-style 5-step structured prompts for Hearout Agent.

References: docs/research/tacit-knowledge-ai-prior-art.md (Kunumi 5-step).
All output strictly JSON to keep ChatExtract deterministic.
"""

HEAROUT_SYSTEM = (
    "You are a tacit-knowledge extraction assistant running a short 5W1H interview. "
    "You must speak in polite Japanese and ask ONE focused question per turn. "
    "Follow the 5-step Kunumi structure: (1) Who/What anchor, (2) When/Where context, "
    "(3) Why intention, (4) How procedure, (5) confirmation. "
    "Stop early if 5W1H is materially complete before turn 5.\n\n"
    "On every turn output strict JSON of the form:\n"
    "{\n"
    "  \"slots\": {\"who\": str|null, \"what\": str|null, \"when\": str|null, "
    "\"where\": str|null, \"why\": str|null, \"how\": str|null},\n"
    "  \"next_question\": str|null,    // Japanese; null when complete\n"
    "  \"complete\": bool,             // true on final turn\n"
    "  \"self_critic\": float,         // 0-10, confidence the extracted slots faithfully capture the user's intent\n"
    "  \"chat_extract_summary\": str   // 1-2 行の確認用要約 (ChatExtract)\n"
    "}\n"
    "If the user replied 'SKIP' or asks to stop, set complete=true and self_critic=0.0."
)


def user_prompt(
    gap_event_id: str,
    sector: str,
    unit: str,
    turn_count: int,
    transcript: list[dict[str, str]],
    latest_answer: str | None,
) -> str:
    """Build the per-turn user message."""
    lines = [
        f"gap_event_id: {gap_event_id}",
        f"sector: {sector}",
        f"unit: {unit}",
        f"これは {turn_count} ターン目 (最大 5 ターン)",
        "----- 会話履歴 -----",
    ]
    for t in transcript:
        role = t.get("role", "?")
        content = t.get("content", "")
        lines.append(f"[{role}] {content}")
    if latest_answer is not None:
        lines.append(f"----- ユーザーの最新回答 -----\n{latest_answer}")
    lines.append("次の質問と現時点の slot 抽出を JSON で返してください。")
    return "\n".join(lines)


INITIAL_QUESTION_FALLBACK = (
    "今のご回答について、もう少し詳しく教えてください。"
    "まず『誰が／何を』の観点で具体的にお願いします。"
)
